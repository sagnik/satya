import os
from typing import Dict, List
from annotate.consts import *
from annotate.data import Token, Content
from annotate.exceptions import ConfigReadError, UnknownFileFormatError, NoFileFoundError


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


def get_file_type(file_name: str):
    """get the file type from the file_name. currently we just check for the extension
    :param file_name:
    :return:
    """
    if not os.path.exists(file_name):
        raise NoFileFoundError(file_name)
    for allowed_file_ext in ALLOWED_FILE_TYPE:
        if file_name.endswith(allowed_file_ext):
            return allowed_file_ext
    raise UnknownFileFormatError(file_name)


def validate(config: Dict):
    """validate the config file for the span annotator, raise exceptions as necessary
    :param config:
    :return:
    """
    entity_names = [entity['name'] for entity in config['entities']]
    if not entity_names:
        raise ConfigReadError(msg='must provide entities')
    for entity_desc in config['entities']:
        if 'name' not in entity_desc:
            raise ConfigReadError(msg='each entity must have a name')
        if entity_desc.get('shortcut') in RESERVED_CHARS:
            raise ConfigReadError(
                msg=f'shortcut {entity_desc.get("shortcut")} for entity {entity_desc["name"]} not allowed because it '
                f'is a reserved character'
            )
    relation_entities = [(relation['name'], relation['entities']) for relation in config.get('relations')]
    for relation_name, entities_this_relation in relation_entities:
        for entity_pair in entities_this_relation:
            start = entity_pair.get('start')
            end = entity_pair.get('end')
            if start is None or end is None:
                raise ConfigReadError(msg=f'Start or End entity not provided for relation {relation_name}')
            if start not in entity_names:
                raise ConfigReadError(
                    msg=f'relation {relation_name} has an entity {start} which is not in the entities list'
                )
            if end not in entity_names:
                raise ConfigReadError(
                    msg=f'relation {relation_name} has an entity {end} which is not in the entities list'
                )
    return


def get_entity_colors(entity_list: List[Dict[str, str]]) -> Dict[str, str]:
    """get the  entity colors. if no color is provided, create own
    :param entity_list:
    :return:
    """
    color_index = 0
    entity_colors = dict()
    for entity_desc in entity_list:
        if 'color' in entity_desc:
            entity_colors[entity_desc['name']] = entity_desc['color']
        else:
            entity_colors[entity_desc['name']] = TKINTER_COLORS[color_index]
            color_index += 1
    return entity_colors
