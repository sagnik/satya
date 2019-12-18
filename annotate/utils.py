from typing import List
from annotate.consts import *
from annotate.data import Token, Content


def towkf(content: Content, output_file: str):
    """
    create a (multi-column) conll file from the content
    :param content:
    :param output_file:
    :return:
    """
    sentence_nums = set([x.sen_index for x in content.tokens])
    sentences: List[List[Token]] = [[x for x in content.tokens if x.sen_index == y] for y in sentence_nums]
    max_num_labels = max([len(token.tags) for token in content.tokens])
    with open(output_file, 'w') as wf:
        for sentence in sentences:
            for token in sentence:
                tags = token.tags + ['O'] * (max_num_labels - len(token.tags))
                tags = ' '.join(tags)
                wf.write(f'{token.content} {tags}\n')
            wf.write(NEW_LINE_CHAR)


def get_file_type(file_name):
    for allowed_file_ext in ALLOWED_FILE_TYPE:
        if file_name.endswith(allowed_file_ext):
            return allowed_file_ext
    return None
