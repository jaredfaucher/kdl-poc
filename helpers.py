import os, zipfile
from shutil import make_archive
from bs4 import BeautifulSoup

INPUT_PATH = 'input'
OUTPUT_PATH = 'output'
TEMPLATE_PATH = 'templates'


# assumes workflow filename == workflow name
def unzip_workflow(input_file):
    zip_ref = zipfile.ZipFile(input_file, 'r')
    zip_ref.extractall(INPUT_PATH)
    zip_ref.close()
    return os.path.splitext(input_file)[0]


def extract_from_input_xml(input_file):
    with open(input_file, "r") as f:
        contents = f.read()
        soup = BeautifulSoup(contents, 'xml')
    node = dict()
    node['name'] = soup.find('entry', key='name')['value']
    model = []

    for child in soup.find('config', key='model').find_all(['config', 'entry'], recursive=False):
        if child.name == 'entry':
            entry = extract_entry_tag(child)
            model.append(entry)
        elif child.name == 'config':
            config = extract_config_tag(child)
            model.append(config)

    node['model'] = model
    return node


def extract_entry_tag(tag):
    entry = {tag['key']: tag['value'], 'type': tag['type']}
    if tag.has_attr('isnull'):
        entry['isnull'] = True
    return entry


def extract_config_tag(tag):
    config_value = []
    for child in tag.children:
        if child.name == 'entry':
            entry = extract_entry_tag(child)
            config_value.append(entry)
        elif child.name == 'config':
            config = extract_config_tag(child)
            config_value.append(config)
    config = {tag['key']: config_value, 'type': 'config'}
    return config


def extract_nodes(input_file):
    node_list = []
    with open(input_file, "r") as f:
        contents = f.read()
        soup = BeautifulSoup(contents, 'xml')

    for child in soup.find('config', key='nodes').find_all('config', recursive=False):
        node = dict()
        node_id = child.find('entry', key='id')['value']
        node['id'] = node_id
        settings_file = child.find('entry', key='node_settings_file')['value']
        node['filename'] = settings_file
        node_list.append(node)
    return node_list


def extract_connections(input_file):
    connection_list = []
    with open(input_file, "r") as f:
        contents = f.read()
        soup = BeautifulSoup(contents, 'xml')

    for child in soup.find('config', key='connections').find_all('config', recursive=False):
        connection = dict()
        source_id = child.find('entry', key='sourceID')['value']
        connection['source_id'] = source_id
        dest_id = child.find('entry', key='destID')['value']
        connection['dest_id'] = dest_id
        source_port = child.find('entry', key='sourcePort')['value']
        connection['source_port'] = source_port
        dest_port = child.find('entry', key='destPort')['value']
        connection['dest_port'] = dest_port
        connection_list.append(connection)
    return connection_list


def create_node_xml_from_template(node):
    template = f'{TEMPLATE_PATH}/{node["name"]}/settings_no_model.xml'
    with open(template, "r") as f:
        contents = f.read()
        soup = BeautifulSoup(contents, 'xml')
    model = soup.find('config', key='model')
    for curr in node['model']:
        if curr['type'] == 'config':
            config = create_config_element(curr)
            model.append(config)
        else:
            entry = create_entry_element(curr)
            model.append(entry)
    return soup


def create_entry_element(entry):
    soup = BeautifulSoup('', 'xml')
    entry_key = list(entry.keys())[0]
    entry_value = entry[entry_key]
    entry_type = entry['type']
    entry_elt = soup.new_tag('entry', key=entry_key, type=entry_type, value=entry_value)
    if 'isnull' in entry:
        entry_elt['isnull'] = 'true'
    return entry_elt


def create_config_element(config):
    soup = BeautifulSoup('', 'xml')
    config_key = list(config.keys())[0]
    config_values = config[config_key]
    config_elt = soup.new_tag('config', key=config_key)
    for value in config_values:
        if value['type'] == 'config':
            child_config = create_config_element(value)
            config_elt.append(child_config)
        else:
            child_entry = create_entry_element(value)
            config_elt.append(child_entry)
    return config_elt


def save_node_xml(tree, output_path):
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    with open(f'{output_path}/settings.xml', 'w') as file:
        file.write(tree.prettify())


def create_output_workflow(workflow_name):
    make_archive(f'{workflow_name}_new', 'zip', OUTPUT_PATH)
    base = os.path.splitext(f'{workflow_name}_new.zip')[0]
    os.rename(f'{workflow_name}_new.zip', base + '.knwf')
