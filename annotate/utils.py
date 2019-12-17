import re
from annotate.consts import *


def is_labeled(content, labels, following_content=''):
    """is the selected text fully labeled?
    For eg:, following contents are invalid:
    'x/I-a y/I-a', 'x/B-a y z/I-a', 'x/B-a y/B-c z/B-a'. Also, if your text is `x/B-a y/I-a` and following
    text is `z/I-a something`, it returns false
    :param content: selected text
    :param following_content: text after selected text
    :param labels: list of labels
    :return: whether the text area is labeled or not
    """
    words = content.split(WORD_SEP)
    if TAG_START_B not in words[0]:
        return False
    last_label = words[0].split(TAG_START_B)[-1]
    if last_label not in labels:
        return False
    for word in words[1:]:
        if not word.endswith(f'{TAG_START_I}{last_label}'):
            return False
    if not following_content:
        return True
    following_word = following_content.strip().split(WORD_SEP)[0]
    if following_word.endswith(f'{TAG_START_I}{last_label}'):
        return False
    return True


def biofy(content, label):
    """biofy a selected string, i.e. `x y z -> x/B-PER y/I-PER z/I-PER`
    :param content: string to biofy
    :param label: label to use
    :return: biofied string
    """
    biofy_words = []
    assert not any([x for x in content.split(' ') if not x])  # no blank space
    for index, word in enumerate(content.split()):
        if index == 0:
            biofy_words.append(f'{word}/B-{label}')
        else:
            biofy_words.append(f'{word}/I-{label}')
    return ' '.join(biofy_words)


def de_biofy(content, depth=1):
    """de-biofy a selected string, i.e. `x/B-PER y/I-PER z/I-PER -> x y z`
    george/B-PER bush/I-PER/B-PRES, depth=1 -> george/B-PER bush/I-PER
    for more example see test_utils.test_de_biofy
    :param content: string to de-biofy.
    :param depth: how many levels of labels to cut
    :return: de-biofied string
    """
    if depth == 0:
        return content
    de_biofied_words = []
    max_depth = max([(word.count('/B-') + word.count('/I-')) for word in content.split()])
    for word in content.split(' '):
        word_tag_depth = word.count('/B-') + word.count('/I-')
        if not ('/B-' in word or '/I-' in word):  # the word has no tag, add it to the list
            de_biofied_words.append(word)
        elif word_tag_depth != max_depth:
            de_biofied_words.append(word)
        else:  # this is a word we can cull
            for index in range(len(word) - 1, 1, -1):
                if word[index - 2] == '/' and (word[index - 1] == 'B' or word[index - 1] == 'I') and word[index] == '-':
                    de_biofied_words.append(word[: index - 2])
                    break
    return de_biofy(' '.join(de_biofied_words), depth=depth - 1)


def towkf_sentence(text, num_column=1):
    """convert a sentence like `Barack/B-PER Obama/I-PER was born in 1961` to [(Barack, B-PER),...]
    The output format is [(word, tag1, tag2...tag_{num_column})]. tags are right padded with O.
    content = Barack/B-PER/B-PRES Obama/I-PER/I-PRES was born in 1961/B-DATE
    num_column = 1 => [(Barack, B-PER), (Obama, I-PER), (was, O), (born, O), (in, O), (1961, B-DATE)]
    num_column = 2 => [(Barack, B-PER, B-PRES), (Obama, I-PER, I-PRES), (was, O, O), (born, O, O), (in, O, O), (1961, B-DATE, O)]
    :param text: text to convert into BIO conll format
    :param num_column: number of columns.
    :return:List[Tuple[word, tags..]]
    """
    tokens = text.split(WORD_SEP)
    token_tags = []
    for index, token in enumerate(tokens):
        if not token:
            print(f'empty word at word index {index} in {text}')
            continue
        if not (TAG_START_B in token or TAG_START_I in token):
            token_tags.append(tuple([token] + ['O'] * num_column))
        else:
            tag_start_end_indices = [(m.start(), m.end()) for m in re.finditer(f'{TAG_START_B}|{TAG_START_I}', token)]
            token_wo_tag = token[: tag_start_end_indices[0][0]]
            if not token_wo_tag:
                print(f'empty word at word index {index} in {text}')
                continue
            tags = []
            for i in range(len(tag_start_end_indices) - 1):
                tag_start = tag_start_end_indices[i][0]
                tag_end = tag_start_end_indices[i + 1][0]
                tag = token[tag_start:tag_end]
                tags.append(tag[1:])
            tag = token[tag_start_end_indices[-1][0] :]
            tags.append(tag[1:])
            if len(tags) >= num_column:
                token_tags.append(tuple([token_wo_tag] + tags[:num_column]))
            else:
                token_tags.append(tuple([token_wo_tag] + tags + ['O'] * (num_column - len(tags))))
    return token_tags


def towkf(content, output_file):
    """
    create a (multi-column) conll file from the content
    :param content:
    :param output_file:
    :return:
    """
    sentences = [x.strip() for x in content.split(NEW_LINE_CHAR) if x.strip()]
    max_tag_depth = max(
        [
            max([(word.count(TAG_START_B) + word.count(TAG_START_I)) for word in sentence.split(WORD_SEP)])
            for sentence in sentences
        ]
    )
    with open(output_file, 'w') as wf:
        for sentence in sentences:
            for word_tags in towkf_sentence(sentence, max_tag_depth):
                word_tags = ' '.join(word_tags)
                wf.write(f'{word_tags}{NEW_LINE_CHAR}')
            wf.write(NEW_LINE_CHAR)
