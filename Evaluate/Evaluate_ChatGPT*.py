import json
import re
from collections import OrderedDict

# Load JSON file
def load_json(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)

def extract_path(answer):
    # Extract path information
    path_match = re.search(r"The path is? ([\d\s\-,>→node]+)", answer)
    if not path_match:  # For sample1
        path_match = re.search(r"The path is simply? ([\d\s\-,>→node]+)", answer, re.IGNORECASE)
    if not path_match:
        path_match = re.search(r"The path is as follows\s+\(([\d\s,]+)\)", answer)
    if not path_match:
        path_match = re.search(r"The path is\s+\(([\d\s,]+)\)", answer)
    if path_match:
        path_str = path_match.group(1)
        # Replace all arrows and connectors to a unified format, and remove 'node' text
        path_str = path_str.replace('node', '').replace('->', '-').replace('→', '-').replace(',', '-').replace(' ', '')
        # Extract all edges
        nodes = [int(node) for node in re.findall(r'\b\d+\b', path_str)]
        return nodes
    return []

def convert_nodes_to_edges_connectivity(nodes):
    edges = []
    for i in range(len(nodes) - 1):
        edges.append((nodes[i], nodes[i + 1]))
    return edges

def extract_cycle(answer):
    answer = answer.replace('\n', '')
    # Match strings that may contain cycles
    cycle_str_match = re.search(r"the cycle is(?: node)?(.*?)(?=[\.\n])", answer, re.IGNORECASE)
    if not cycle_str_match:
        cycle_str_match = re.search(r"the cycle with the fewest number of nodes(.*?)(?=(?:Yes.*?\.)|which|$)", answer, re.IGNORECASE)
    if not cycle_str_match:
        print("***")
    if cycle_str_match:
        cycle_str = cycle_str_match.group(1)
        # Replace all arrows and connectors to a unified format
        cycle_str = cycle_str.replace('->', '-').replace('→', '-').replace(',', '-').replace(' ', '')
        # Remove all non-digit characters, except separators
        cycle_str = re.sub(r"[^\d,\- >→]", '', cycle_str)
        # Split the string into a list of nodes
        nodes = cycle_str.split('-')
        # Filter out nodes that cannot be converted to integers
        filtered_nodes = [node for node in nodes if node.isdigit()]
        # Convert the list of nodes to a tuple of edges
        # print(filtered_nodes)
        edges = convert_nodes_to_edges_cycle(list(map(int, filtered_nodes)))
        return edges
    # Match the case where only a sequence of numbers is given
    cycle_str_match = re.search(r"The cycle is (\d+(?:, \d+)*).", answer)
    if cycle_str_match:
        cycle_str = cycle_str_match.group(1)
        nodes = [int(node.strip()) for node in cycle_str.split(',')]
        edges = convert_nodes_to_edges_cycle(nodes)
        return edges
    return []

def convert_nodes_to_edges_cycle(nodes):
    edges = OrderedDict()  # Use OrderedDict to store edges to avoid duplication and maintain order
    for i in range(len(nodes) - 1):
        if nodes[i] != nodes[i + 1]:
            # Use a sorted tuple as the key to ensure the direction of the edge does not affect deduplication
            edge = tuple((nodes[i], nodes[i + 1]))
            edges[edge] = None  # The value is not important, what matters is the order and uniqueness of the key
    # If the cycle is not closed, add an edge from the last node to the first node
    if len(nodes) > 1 and nodes[0] != nodes[-1]:
        edge = tuple((nodes[-1], nodes[0]))
        edges[edge] = None
    return list(edges.keys())  # Return an ordered list of edges

def extract_shortest_path_and_weight(answer):
    sentences = re.split(r'[\.\n]', answer)
    last_sentence = sentences[-2].strip() if len(sentences) > 1 else answer.strip()
    path = []
    # Special case, equivalent to a patch
    if "either" in last_sentence and "or" in last_sentence and "through" in last_sentence:
        either_or_match = re.search(r'or\s+(.*?)\s+with', last_sentence, re.IGNORECASE)
        through_match = re.search(r'from node (\d+)\s+to node (\d+)', last_sentence, re.IGNORECASE)
        if either_or_match and through_match:
            through_nodes = either_or_match.group(1).replace('node', '').replace('Node', '')
            start, end = through_match.groups()
            path = [int(start)] + [int(node.strip()) for node in through_nodes.split(',') if node.strip().isdigit()] + [int(end)]
    elif "either" in last_sentence and "or" in last_sentence:
        either_or_match = re.search(r'either\s+(.*?)\s+or', last_sentence, re.IGNORECASE)
        if either_or_match:
            path_str = either_or_match.group(1).replace('->', ',').replace('→', ',').replace('-', ',')
            path = [int(node.strip()) for node in path_str.split(',') if node.strip().isdigit()]
    elif "through" in last_sentence:
        through_match = re.search(r'from node (\d+)\s+to node (\d+).*?through\s+(.*?)\s+(?:with|\.|$)', last_sentence, re.IGNORECASE)
        if through_match:
            start, end, through_nodes = through_match.groups()
            through_nodes = through_nodes.replace('node', '').replace('Node', '')  # Remove 'node'
            path = [int(start)] + [int(node.strip()) for node in through_nodes.split(',') if node.strip().isdigit()] + [int(end)]
    elif "directly" in last_sentence:
        directly_match = re.search(r'from node (\d+)\s+to node (\d+)', last_sentence, re.IGNORECASE)
        if directly_match:
            path = [int(directly_match.group(1)), int(directly_match.group(2))]
    # Extract the path
    else:
        path_match = re.search(r'is\s+(.*?)(?:\s+with|\.|$)', last_sentence, re.IGNORECASE)
        if path_match:
            path_str = path_match.group(1)
            path = [int(node) for node in re.findall(r'\b\d+\b', path_str)]
    # Extract the weight
    weight_match = re.search(r'total weight(?: is)?[^\d]*(\d+)', last_sentence, re.IGNORECASE)
    weight = int(weight_match.group(1)) if weight_match else 0
    return path, weight

def extract_hamiltonpath(answer):
    # Extract the Hamilton path
    path_str_match = re.search(r"the path is(?: node)?(.*?)(?=(?:Yes.*?\.)|which|$)", answer, re.IGNORECASE)
    if not path_str_match:
        print("***")
    if path_str_match:
        path_str = path_str_match.group(1)
        # Replace all arrows and connectors to a unified format
        path_str = path_str.replace('->', '-').replace('→', '-').replace(',', '-').replace(' ', '')
        # Remove all non-digit characters, except separators
        path_str = re.sub(r"[^\d,\- >→]", '', path_str)
        # Split the string into a list of nodes
        nodes = path_str.split('-')
        # Filter out nodes that cannot be converted to integers
        filtered_nodes = [node for node in nodes if node.isdigit()]
        # Convert the list of nodes to a tuple of edges
        # print(filtered_nodes)
        edges = convert_nodes_to_edges_hamiltonpath(list(map(int, filtered_nodes)))
        return edges
    # Match the case where only a sequence of numbers is given
    path_str_match = re.search(r"The path is (\d+(?:, \d+)*).", answer)
    if path_str_match:
        path_str = path_str_match.group(1)
        nodes = [int(node.strip()) for node in path_str.split(',')]
        edges = convert_nodes_to_edges_hamiltonpath(nodes)
        return edges
    return []

def convert_nodes_to_edges_hamiltonpath(nodes):
    edges = OrderedDict()  # Use OrderedDict to store edges to prevent duplication and maintain order
    for i in range(len(nodes) - 1):
        if nodes[i] != nodes[i + 1]:
            # Use a sorted tuple as the key to ensure the direction of the edge does not affect deduplication
            edge = tuple((nodes[i], nodes[i + 1]))
            edges[edge] = None  # The value is not important, what matters is the order and uniqueness of the key
    return list(edges.keys())  # Return an ordered list of edges

def compare_answers_connectivity(result_answer, standard_answer, qid):
    # Check the accuracy of yes/no
    result_yes_no = "yes" if ("yes" in result_answer.lower() or "there is a path" in result_answer.lower()) else ("no" if "no," in result_answer.lower() or "there is no path" in result_answer.lower() else None)
    standard_yes_no = "yes" if ("yes" in standard_answer.lower()) else "no"
    # If neither "yes" nor "no" is in the result
    if result_yes_no is None:
        return False, False
    roughly_correct = bool(result_yes_no == standard_yes_no)
    # If the answer is "yes", check if the cycle actually exists
    if result_yes_no == "yes":
        result_path = extract_path(result_answer)
        result_edges = convert_nodes_to_edges_connectivity(result_path)
        # Get the edges of the graph
        graph_data = standard_data[int(qid)]
        edges_str = graph_data["conversations"][3]["value"]
        edges_str = edges_str.split("The edges are represented by the tuples:\n")[1]
        edge_strs = edges_str.split("), (")
        edges = [tuple(map(int, edge.replace("(", "").replace(")", "").split(", "))) for edge in edge_strs]
        # Check if each edge exists in the graph
        for edge in result_edges:
            if not any(set(edge) == {u, v} for (u, v) in edges):
                return roughly_correct, False
        if len(result_edges) < 1:
            return roughly_correct, False
        print(f"Yes: No {qid}")
        print(result_edges)
        return True, True
    if result_yes_no == standard_yes_no:
        print(f"No: No {qid}")
    return roughly_correct, result_yes_no == standard_yes_no

def compare_answers_cycle(result_answer, standard_answer, qid):
    # Check the accuracy of yes/no
    result_yes_no = "yes" if ("yes" in result_answer.lower() or "there is a cycle" in result_answer.lower()) else ("no" if "no," in result_answer.lower() or "there is no cycle" in result_answer.lower() else None)
    standard_yes_no = "yes" if ("yes" in standard_answer.lower()) else "no"
    # If neither "yes" nor "no" is in the result
    if result_yes_no is None:
        return False, False
    roughly_correct = bool(result_yes_no == standard_yes_no)
    # If the answer is "yes", check if the cycle actually exists
    if result_yes_no == "yes":
        result_cycle = extract_cycle(result_answer)
        # Get the edges of the graph
        graph_data = standard_data[int(qid)]
        edges_str = graph_data["conversations"][3]["value"]
        edges_str = edges_str.split("The edges are represented by the tuples:\n")[1]
        edge_strs = edges_str.split("), (")
        edges = [tuple(map(int, edge.replace("(", "").replace(")", "").split(", "))) for edge in edge_strs]
        # Check if each edge exists in the graph
        for edge in result_cycle:
            if not any(set(edge) == {u, v} for (u, v) in edges):
                return roughly_correct, False
        if len(result_cycle) < 2:
            return roughly_correct, False
        print(f"Yes: No {qid}")
        print(result_cycle)
        return True, True
    if result_yes_no == standard_yes_no:
        print(f"No: No {qid}")
    return roughly_correct, result_yes_no == standard_yes_no

def compare_answers_shortestpath(result_answer, standard_answer, qid):
    result_path, result_weight = extract_shortest_path_and_weight(result_answer)
    standard_path, standard_weight = extract_shortest_path_and_weight(standard_answer)
    # Print the standard path
    # print(standard_path)
    if result_weight != standard_weight:
        return False
    # Get data corresponding to the ID
    graph_data = standard_data[int(qid) - 135]
    # Get the edges of the graph and properly handle the string format
    edges_str = graph_data["conversations"][3]["value"]
    edges_str = edges_str.split("The edges are represented by the tuples:\n")[1]
    edge_strs = edges_str.split("), (")
    edges = [tuple(map(int, edge.replace("(", "").replace(")", "").split(", "))) for edge in edge_strs]
    # Extract the nodes and weights from the generated path
    result_path_nodes = result_path
    result_path_edges = [(result_path_nodes[i], result_path_nodes[i + 1]) for i in range(len(result_path_nodes) - 1)]
    # Check if the path exists in the graph and calculate the total weight of the path
    total_weight = 0
    for edge in result_path_edges:
        # Find the edge in the graph
        found_edge = next(((u, v, w) for (u, v, w) in edges if set(edge) == {u, v}), None)
        if not found_edge:
            return False
        total_weight += found_edge[2]
    # Compare the total weight of the path with the generated weight
    if (total_weight == result_weight):
        print(f"No {qid}")
        print(result_path)
        print(total_weight)
    return total_weight == result_weight

def compare_answers_hamiltonpath(result_answer, standard_answer, qid):
    # Check the accuracy of yes/no
    result_yes_no = "yes" if ("yes" in result_answer.lower()) else ("no" if ("no," in result_answer.lower() or "no path" in result_answer.lower()) else None)
    standard_yes_no = "yes" if ("yes" in standard_answer.lower()) else "no"
    # If neither "yes" nor "no" is in the result
    if result_yes_no is None:
        return False
    # If the answer is "yes", check if the cycle actually exists
    if result_yes_no == "yes":
        result_path = extract_hamiltonpath(result_answer)
        # Get the nodes and edges of the graph
        graph_data = standard_data[int(qid) - 277]
        node_str = graph_data["conversations"][1]["value"]  # There are 8 nodes in the diagram.
        node_count_match = re.search(r"There are (\d+) nodes", node_str)
        node_count = int(node_count_match.group(1))
        all_nodes = set(range(node_count))
        nodes_in_path = set()
        edges_str = graph_data["conversations"][3]["value"]
        edges_str = edges_str.split("The edges are represented by the tuples:\n")[1]
        edge_strs = edges_str.split("), (")
        edges = [tuple(map(int, edge.replace("(", "").replace(")", "").split(", "))) for edge in edge_strs]
        # Check if each edge exists in the graph
        for edge in result_path:
            if not any(set(edge) == {u, v} for (u, v) in edges):
                return False
            nodes_in_path.update(edge)
        if nodes_in_path != all_nodes:
            return False
        if len(result_path) < 1:
            return False
        print(f"Yes: No {qid}")
        print(result_path)
        return True
    if result_yes_no == standard_yes_no:
        print(f"No: No {qid}")
    return result_yes_no == standard_yes_no

# Load data
results_data = load_json('/path/to/results.json')
standard_data = load_json('/path/to/standard.json') # standard.json can be composed of test.json files under /VisionGraph/Dataset

# Initialize counters
accuracies = {
    "Connectivity": {
        "easy": {"segment3": 0, "segment3_rough": 0},
        "medium": {"segment3": 0, "segment3_rough": 0},
        "hard": {"segment3": 0, "segment3_rough": 0}
    },
    "Cycle": {
        "easy": {"segment3": 0, "segment3_rough": 0},
        "medium": {"segment3": 0, "segment3_rough": 0},
        "hard": {"segment3": 0, "segment3_rough": 0}
    },
    "ShortestPath": {"easy": 0, "hard": 0},
    "HamiltonPath": {"easy": 0, "hard": 0}
}
question_num = {
    "Connectivity": {"easy": 0, "medium": 0, "hard": 0},
    "Cycle": {"easy": 0, "medium": 0, "hard": 0},
    "ShortestPath": {"easy": 0, "hard": 0},
    "HamiltonPath": {"easy": 0, "hard": 0}
}

# Compare the answers
for result in results_data:
    qid = result["id"]
    if(int(qid) <= 561):
        standard = standard_data[int(qid)]
    elif(int(qid) >= 903):
        standard = standard_data[int(qid) - 277]
    else:
        standard = standard_data[int(qid) - 135]
    difficulty = standard["difficulty"]
    category = result["image_url"].split('/')[6].split('_')[0]
    if category == 'HamlitonPath':
        category = 'HamiltonPath'
    question_num[category][difficulty] += 1
    result_answer = result["segment3"]
    standard_answer = standard["conversations"][5]["value"]
    if category == 'Connectivity':
        rough_correct, exact_correct = compare_answers_connectivity(result_answer, standard_answer, qid)
        if rough_correct:
            accuracies[category][difficulty]["segment3_rough"] += 1
        if exact_correct:
            accuracies[category][difficulty]["segment3"] += 1
    elif category == 'Cycle':
        rough_correct, exact_correct = compare_answers_cycle(result_answer, standard_answer, qid)
        if rough_correct:
            accuracies[category][difficulty]["segment3_rough"] += 1
        if exact_correct:
            accuracies[category][difficulty]["segment3"] += 1
    elif category == 'ShortestPath':
        if(compare_answers_shortestpath(result_answer, standard_answer, qid)):
            accuracies[category][difficulty] += 1
    elif category == 'HamiltonPath':
        if(compare_answers_hamiltonpath(result_answer, standard_answer, qid)):
            accuracies[category][difficulty] += 1

# Print results
for category in accuracies:
    print(f"Category: {category}")
    for difficulty in accuracies[category]:
        # Check if the number of questions is 0
        if question_num[category][difficulty] == 0:
            continue
        if (category == 'ShortestPath' or category == 'HamiltonPath'):
            accuracy = accuracies[category][difficulty] / question_num[category][difficulty]
            print(f"  {difficulty} Accuracy: {accuracy:.4f}")
        else:
            for segment in ["segment3", "segment3_rough"]:
                accuracy = accuracies[category][difficulty][segment] / question_num[category][difficulty]
                print(f"  {difficulty} {segment} Accuracy: {accuracy:.4f}")
