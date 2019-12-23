# code for data models
from typing import Dict, Set, List, Union, Tuple
import json
from annotate.consts import WORD_SEP, DEFAULT_HIGHLIGHT_COLOR, NEW_LINE_CHAR
from collections import namedtuple

Relation = namedtuple('relation', ['start', 'end', 'name', 'color'])


class Tag:
    def __init__(self, content: str, color: str = DEFAULT_HIGHLIGHT_COLOR):
        self.content = content
        self.color = color

    def serialize(self) -> Dict:
        return {'content': self.content, 'color': self.color}


class Token:
    def __init__(
        self, content: str, sen_index: int, tok_index: int, char_start_index: int, char_end_index: int, **kwargs
    ):
        assert content.strip()
        self.content = content
        self.sen_index = sen_index
        self.tok_index = tok_index
        self.char_start_index = char_start_index
        self.char_end_index = char_end_index
        self.id: str = kwargs.get('id', f'{self.sen_index}:{self.tok_index}')
        self.tags: List[str] = kwargs.get('tag', [])

    def serialize(self) -> Dict:
        return {
            'content': self.content,
            'sen_index': self.sen_index,
            'tok_index': self.tok_index,
            'char_start_index': self.char_start_index,
            'char_end_index': self.char_end_index,
            'id': self.id,
            'tags': self.tags,
        }


class Span:
    def __init__(self, **kwargs):
        tokens: List[Token] = kwargs.get('tokens', [])
        if tokens:
            assert len(set([x.sen_index for x in tokens])) == 1  # all tokens come from the same sentence
            tok_indices = [x.tok_index for x in tokens]
            for index in range(1, len(tok_indices)):
                if (tok_indices[index] - tok_indices[index - 1]) != 1:  # all tokens must be contiguous
                    assert False
            self.sen_index = [x.sen_index for x in tokens][0]
            self.tok_start_index = tokens[0].tok_index
            self.tok_end_index = tokens[-1].tok_index
            self.content = ' '.join([x.content for x in tokens])
            self.char_start_index = tokens[0].char_start_index
            self.char_end_index = tokens[-1].char_end_index
        else:
            self.sen_index = kwargs['sen_index']
            self.tok_start_index = kwargs['tok_start_index']
            self.tok_end_index = kwargs['tok_end_index']
            self.content = kwargs['content']
            self.char_start_index = kwargs['char_start_index']
            self.char_end_index = kwargs['char_end_index']
        self.tags: List[Tag] = kwargs.get('tags', [])
        self.id = kwargs.get('id', f'{self.sen_index}:{self.tok_start_index}:{self.tok_end_index}')

    def add_tag(self, tag: Tag):
        """add a label to the span
        :param tag:
        :return:
        """
        if tag.content not in [tag.content for tag in self.tags]:
            self.tags.append(tag)

    def serialize(self) -> Dict:
        return {
            'sen_index': self.sen_index,
            'tok_start_index': self.tok_start_index,
            'tok_end_index': self.tok_end_index,
            'content': self.content,
            'char_start_index': self.char_start_index,
            'char_end_index': self.char_end_index,
            'tags': [tag.serialize() for tag in self.tags],
            'id': self.id,
        }


class Content:
    """
    Full text that is being annotated
    """

    def __init__(self, **kwargs):
        self.tokens: List[Token] = kwargs.get('tokens', [])  # should really be an ordered set
        self.spans: Set[Span] = set(kwargs.get('spans', []))
        self.relations: Set[Relation] = set(kwargs.get('relations', []))
        self.tokens_spans: List[Tuple[str, str]] = kwargs.get('tokens_spans', [])

    def populate_from_json(self, json_file: str):
        """populate the content from a json file
        :return:
        """
        content = json.load(open(json_file))
        self.populate_from_dict(content)

    def populate_from_dict(self, content: Dict):
        """populate the content from a dict
        :param content:
        :return:
        """
        self.tokens = [Token(**t) for t in content.get('tokens', [])]
        self.spans = set(
            [
                Span(
                    sen_index=s['sen_index'],
                    tok_start_index=s['tok_start_index'],
                    tok_end_index=s['tok_end_index'],
                    content=s['content'],
                    char_start_index=s['char_start_index'],
                    char_end_index=s['char_end_index'],
                    tags=[Tag(**t) for t in s['tags']],
                    id=s['id'],
                )
                for s in content.get('spans', [])
            ]
        )
        self.relations = set([Relation(**r) for r in content.get('relations', [])])
        self.tokens_spans = content.get('tokens_spans', [])

    def populate_from_text(self, txt_file):
        """
        populate the content from a text file
        :return:
        """
        with open(txt_file, 'r') as f:
            for line_num, line in enumerate(f):
                if line.endswith(NEW_LINE_CHAR):
                    line = line[:-1]
                char_index = 0
                for word_num, word in enumerate(line.split(WORD_SEP)):
                    token = Token(
                        content=word,
                        sen_index=line_num + 1,
                        tok_index=word_num,
                        char_start_index=char_index,
                        char_end_index=char_index + len(word),
                    )
                    char_index = char_index + len(word) + 1
                    self.tokens.append(token)

    def add_tag(self, tag: Tag, sen_index: int, char_start_index: int, char_end_index: int):
        """add a label to a span
        :param tag:
        :param sen_index:
        :param char_start_index:
        :param char_end_index:
        :return:
        """
        # which span have we selected?
        tokens = []
        for token in self.tokens:
            if (
                token.sen_index == sen_index
                and token.char_start_index >= char_start_index
                and token.char_end_index <= char_end_index
            ):
                tokens.append(token)
        if not tokens:
            raise RuntimeError('can not add tag when no token is selected')
        tokens.sort(key=lambda x: x.tok_index)
        spans = [
            span for span in self.spans if span.id == f'{span.sen_index}:{tokens[0].tok_index}:{tokens[-1].tok_index}'
        ]
        assert len(spans) <= 1
        new_span = False
        if spans:
            span = self.span_from_span_id(spans[0].id)
            span.add_tag(tag)
        else:
            span = Span(tokens=tokens, tags=[tag])
            self.spans.add(span)
            new_span = True
        for index, token in enumerate(tokens):
            if new_span:
                self.tokens_spans.append((f'{token.id}', f'{span.id}'))
            if index == 0:
                token.tags.append(f'B-{tag.content}')
            else:
                token.tags.append(f'I-{tag.content}')

    def delete_tag(self, span: Span, tag: Tag):
        """delete the tag from a span
        :param span:
        :param tag:
        :return:
        """
        for tag_ in span.tags:
            if tag_.content == tag.content:
                span.tags.remove(tag_)
        span_id = span.id
        for token_id_, span_id_ in self.tokens_spans:
            if span_id_ == span_id:
                token = self.token_from_token_id(token_id_)
                if f'B-{tag.content}' in token.tags:
                    token.tags.remove(f'B-{tag.content}')
                else:
                    token.tags.remove(f'I-{tag.content}')
        if not span.tags:
            self.spans.remove(span)
            self.tokens_spans = [
                (token_id_, span_id_) for token_id_, span_id_ in self.tokens_spans if span_id_ != span_id
            ]

    def token_from_token_id(self, id_: str) -> Union[Token, None]:
        """get token from token id
        :param id_: token id
        :return:
        """
        _tokens = [x for x in self.tokens if x.id == id_]
        if not _tokens:
            return None
        else:
            return _tokens[0]

    def span_from_span_id(self, id_: str) -> Union[Span, None]:
        """get span from span id
        :param id_: span id
        :return:
        """
        _spans = [x for x in self.spans if x.id == id_]
        if not _spans:
            return None
        else:
            return _spans[0]

    def token_id_from_token(self, token: Token) -> Union[str, None]:
        """get token id from token
        :param token: token
        :return:
        """
        _tokens = [x for x in self.tokens if x == token]
        if not _tokens:
            return None
        else:
            return _tokens[0].id

    def span_id_from_start_end_index(self, sen_index: int, start_index: int, end_index: int) -> Union[str, None]:
        """get the id for a span from given start and end char indices
        :param sen_index:
        :param start_index:
        :param end_index:
        :return:
        """
        spans = [
            x
            for x in self.spans
            if x.sen_index == sen_index and x.char_start_index == start_index and x.char_end_index == end_index
        ]
        if not spans:
            return None
        assert len(spans) == 1
        return spans[0].id

    def token_id_from_char_index(self, sen_index: int, char_index: int) -> Union[str, None]:
        """get token id from the cursor position
        :param sen_index: sentence index
        :param char_index: cursor position in the sentence
        :return:
        """
        for token in self.tokens:
            if token.sen_index == sen_index and token.char_start_index <= char_index <= token.char_end_index:
                return token.id
        return None

    def span_ids_from_char_index(self, sen_index: int, char_index: int) -> List[str]:
        """get possible spans from a cursor position. There can be more than one span for a token
        :param sen_index: sentence index
        :param char_index: cursor position in the index
        :return:
        """
        token_id = self.token_id_from_char_index(sen_index, char_index)
        if token_id is None:
            return []
        else:
            return self.span_ids_from_token_id(token_id)

    def span_id_from_span(self, span: Span) -> Union[str, None]:
        _spans = [x for x in self.spans if x == span]
        if not _spans:
            return None
        else:
            return _spans[0].id

    def is_token_in_span(self, token_id: str, span_id: str) -> bool:
        """is the token in the span?
        :param token_id:
        :param span_id:
        :return:
        """
        for token_id_, span_id_ in self.tokens_spans:
            if token_id_ == token_id and span_id_ == span_id:
                return True
        return False

    def span_ids_from_token_id(self, token_id: str) -> List[str]:
        return list(set([span_id_ for token_id_, span_id_ in self.tokens_spans if token_id_ == token_id]))

    def serialize(self) -> Dict:
        """
        convert it to a dict to be serialized for later
        :return:
        """
        dict_ = dict()
        dict_['tokens'] = [token.serialize() for token in self.tokens]
        dict_['spans'] = [span.serialize() for span in self.spans]
        dict_['tokens_spans'] = list(self.tokens_spans)
        return dict_
