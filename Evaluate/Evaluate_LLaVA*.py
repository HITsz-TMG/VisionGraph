import json
import re
from tqdm import tqdm

def load_dataset(json_file):
    """Load answers from a JSON file"""
    with open(json_file, 'r') as file:
        data = json.load(file)
    return data

def extract_numbers(text):
    """Extract numbers from text"""
    return re.findall(r'\d+', text)

def extract_tuples(text):
    """Extract tuples or angle-bracket expressions from text and handle specific string patterns"""
    tuples = re.findall(r'\((.*?)\)|<(.*?)>', text)
    extracted_tuples = []
    for t in tuples:
        t = t[0] if t[0] else t[1]
        # Use regular expression to extract numbers
        numbers = re.findall(r'\d+', t)
        # Convert extracted numbers to integers and create a tuple
        extracted_tuples.append(tuple(map(int, numbers)))
    return extracted_tuples

def get_expected_answer(expected_data, id, segment):
    """Get the expected answer for a given id"""
    for item in expected_data:
        if item['id'] == id:
            if(segment == 'segment1'):
                return item['conversations'][1]['value']
            elif(segment == 'segment2'):
                return item['conversations'][3]['value']
            elif(segment == 'segment3'):
                return item['conversations'][5]['value']
    return None

def text_to_num(text):
    num_dict = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9
    }
    return num_dict.get(text.lower(), None)

def compare_answers(result_answer, standard_answer, category):
    result_tuples = extract_tuples(result_answer)
    standard_tuples = extract_tuples(standard_answer)
    correct = set(result_tuples).intersection(set(standard_tuples))
    incorrect = set(result_tuples).difference(set(standard_tuples))
    correct_rate = len(correct) / len(standard_tuples) if standard_tuples else 0
    error_rate = len(incorrect) / len(result_tuples) if result_tuples else 0
    half_correct = 1 if correct_rate >= 0.5 else 0
    return correct_rate, error_rate, half_correct

def is_correct_answer(generated, expected, segment, category, id):
    if segment == 'segment1':
        gen_numbers = extract_numbers(generated)
        exp_numbers = extract_numbers(expected)
        if not gen_numbers:
            gen_numbers = [text_to_num(word) for word in generated.split() if text_to_num(word) is not None]
        return gen_numbers == exp_numbers
    elif segment == 'segment2':
        # Extract tuples in the second question and compare sets (ignore order)
        return set(extract_tuples(generated)) == set(extract_tuples(expected))
    else:
        # Remove extra spaces and newline characters to simplify comparison
        if category != "BipartiteGraphMatching":
            generated = generated.replace("\n", "").replace(" ", "")
            expected = expected.replace("\n", "").replace(" ", "")
        # Compare answers based on different categories
        if category in ["Connectivity", "Cycle"]:
            try:
                # Extract and compare the keywords "Yes" or "No"
                return (("yes" in generated.lower()) == ("yes" in expected.lower()))
            except Exception as e:
                print("One mistake happens in CC:", e)
                return False
        elif category == "TopologicalSort":
            try:
                # Extract the number of nodes and edges
                graph_data = expected_data[int(id)]
                nodes_str = graph_data["conversations"][1]["value"]
                nodes_num = int(re.search(r"There are (\d+) nodes", nodes_str).group(1))
                edges_str = graph_data["conversations"][3]["value"]
                edges = [tuple(map(int, re.findall(r'(\d+), (\d+)', edge)[0])) for edge in edges_str.split(">, <")]
                # Extract the generated topological sort
                gen_order = [int(node) for node in re.findall(r'\d+', generated)]
                # Check if the number of nodes is consistent
                if len(gen_order) != nodes_num:
                    return False
                # Check if the topological sort satisfies the constraints of the edges
                for index, node in enumerate(gen_order):
                    # Find all edges pointing to the current node
                    incoming_edges = [u for u, v in edges if v == node]
                    # Check if all source nodes pointing to the current node have been traversed in the topological sort
                    for source_node in incoming_edges:
                        if source_node not in gen_order[:index]:
                            return False
                return True
            except Exception as e:
                print("One mistake happens in TopologicalSort:", e)
                return False
        elif category == "ShortestPath":
            try:
                # Extract the path and total weight and compare
                gen_path = generated.split("is")[1].split("with")[0].strip()
                # print(gen_path)
                gen_weight = generated.split("of")[1].strip()
                # print(gen_weight)
                exp_weight = expected.split("of")[1].strip()
                # If the total weight is not equal, return False
                if gen_weight != exp_weight:
                    return False
                # Get data corresponding to the ID
                graph_data = expected_data[int(id)]
                # Get the edges of the graph and properly handle the string format
                edges_str = graph_data["conversations"][3]["value"]
                edges_str = edges_str.split("The edges are represented by the tuples:\n")[1]
                edge_strs = edges_str.split("), (")
                edges = [tuple(map(int, edge.replace("(", "").replace(")", "").split(", "))) for edge in edge_strs]
                # Extract the nodes and weights from the generated path
                gen_path_nodes = [int(node) for node in gen_path.split(",")]
                gen_path_edges = [(gen_path_nodes[i], gen_path_nodes[i + 1]) for i in range(len(gen_path_nodes) - 1)]
                # Check if the path exists in the graph and calculate the total weight of the path
                total_weight = 0
                for edge in gen_path_edges:
                    # Find the edge in the graph
                    found_edge = next(((u, v, w) for (u, v, w) in edges if set(edge) == {u, v}), None)
                    if not found_edge:
                        return False
                    total_weight += found_edge[2]
                # Compare the total weight of the path with the generated weight
                return str(total_weight) == gen_weight
            except Exception as e:
                print("An error occurred in ShortestPath:", e)
            return False
        elif category == "BipartiteGraphMatching":
            try:
                # Extract the matching of applicants and jobs
                gen_matches = re.findall(r"applicant (\d+): job (\d+)", generated)
                # Check for duplicate applicants or jobs
                applicants = set()
                jobs = set()
                for applicant, job in gen_matches:
                    if applicant in applicants or job in jobs:
                        return False
                    applicants.add(applicant)
                    jobs.add(job)
                # Convert to dictionary form
                gen_matches_dict = dict(gen_matches)
                gen_count = re.search(r"(\d+) applicants can f", generated).group(1)
                exp_count = re.search(r"(\d+) applicants can f", expected).group(1)
                # Check if the number of applicants matches
                if gen_count != exp_count:
                    return False
                # Get data corresponding to the ID
                graph_data = expected_data[int(id)]
                edges_str = graph_data["conversations"][3]["value"]
                # Check if each applicant-job pair exists in edges_str
                for applicant, job in gen_matches_dict.items():
                    if f"(Appl{applicant}, Job{job})" not in edges_str:
                        return False
                return True
            except Exception as e:
                print("An error occurred in BipartiteGraphMatching:", e)
                return False
        elif category == "MaximumFlow":
            try:
                # Extract and compare the value of the maximum flow
                gen_flow = re.search(r"Themaximumflowfromnode\d+tonode\d+is(\d+).", generated).group(1)
                exp_flow = re.search(r"Themaximumflowfromnode\d+tonode\d+is(\d+).", expected).group(1)
                return gen_flow == exp_flow
            except Exception as e:
                print("An error occurred in MaximumFlow:", e)
                return False
        elif category == "HamiltonPath":
            try:
                if "canbe:" in generated:
                    gen_path_nodes = [int(node) for node in re.findall(r'\d+', generated.split("canbe:")[1])]
                else:
                    gen_path_nodes = [int(node) for node in re.findall(r'\d+', generated.split("pathis")[1])]
                # Get data corresponding to the ID
                graph_data = expected_data[int(id)]
                # Extract the number of nodes and edges
                nodes_str = graph_data["conversations"][1]["value"]
                nodes_num = int(re.search(r"(\d+) nodes", nodes_str).group(1))
                edges_str = graph_data["conversations"][3]["value"]
                edges_str = edges_str.split("The edges are represented by the tuples:\n")[1]
                edge_strs = edges_str.split("), (")
                edges = [set(map(int, edge.replace("(", "").replace(")", "").split(", "))) for edge in edge_strs]
                # Check if the path covers all nodes
                if len(set(gen_path_nodes)) != nodes_num:
                    return False
                # Check if each edge on the path exists
                for i in range(len(gen_path_nodes) - 1):
                    edge = {gen_path_nodes[i], gen_path_nodes[i + 1]}
                    if edge not in edges:
                        return False
                return True
            except Exception as e:
                print("An error occurred in HamiltonPath:", e)
                return False
        elif category == "GNN":
            try:
                # Split by 'node' and compare each one by one
                gen_lines = generated.split("node")
                exp_lines = expected.split("node")
                if len(gen_lines) < 2:
                    return False
                for gen_line, exp_line in zip(gen_lines[1:], exp_lines[1:]):
                    if gen_line != exp_line:
                        return False
                return True
            except Exception as e:
                print("An error occurred in GNN:", e)
                return False
        else:
            return False

# Load the generated and expected answers
generated_data = load_dataset('/path/to/results.json')
expected_data = load_dataset('/path/to/standard.json') # standard.json can be composed of test.json files under /VisionGraph/Dataset
# Initialize statistics
accuracy_stats = {}
total_accuracy_stats = {}
segment2_additional_stats = {}  # Additional statistics for segment2
category_total_stats_segment2 = {}

# Iterate over each sample in the dataset
for data in tqdm(generated_data):
    id = data["id"]
    category = data["image_url"].split('/')[5]  # Extract category, e.g., 'Cycle'
    difficulty = data["difficulty"]  # Extract difficulty
    # Process each segment
    for segment in ["segment1", "segment2", "segment3"]:
        generated_answer = data[segment]
        expected_answer = get_expected_answer(expected_data, id, segment)
        # If an answer is not found, skip it
        if generated_answer is None or expected_answer is None:
            continue
        # Initialize statistics for difficulty
        difficulty_segment_key = f"{category}_{difficulty}_{segment}"
        if difficulty_segment_key not in accuracy_stats:
            accuracy_stats[difficulty_segment_key] = {'correct': 0, 'total': 0}
        # Initialize total statistics
        total_key = f"{category}_total_{segment}"
        if total_key not in total_accuracy_stats:
            total_accuracy_stats[total_key] = {'correct': 0, 'total': 0}
        # Check if the answer is correct
        is_correct = is_correct_answer(generated_answer, expected_answer, segment, category, id)
        accuracy_stats[difficulty_segment_key]['correct'] += int(is_correct)
        accuracy_stats[difficulty_segment_key]['total'] += 1
        total_accuracy_stats[total_key]['correct'] += int(is_correct)
        total_accuracy_stats[total_key]['total'] += 1
        if segment == 'segment2':
            # Calculate additional metrics for segment2
            correct_rate, error_rate, half_correct = compare_answers(generated_answer, expected_answer, category)
            segment2_key = f"{category}_{difficulty}_segment2_additional"
            if segment2_key not in segment2_additional_stats:
                segment2_additional_stats[segment2_key] = {'correct_rate': [], 'error_rate': [], 'half_correct': 0}
            segment2_additional_stats[segment2_key]['correct_rate'].append(correct_rate)
            segment2_additional_stats[segment2_key]['error_rate'].append(error_rate)
            segment2_additional_stats[segment2_key]['half_correct'] += half_correct
            # Aggregate statistics for each category of segment2
            category_key = f"{category}_segment2_total"
            if category_key not in category_total_stats_segment2:
                category_total_stats_segment2[category_key] = {'correct_rate': [], 'error_rate': [], 'half_correct': 0}
            category_total_stats_segment2[category_key]['correct_rate'].append(correct_rate)
            category_total_stats_segment2[category_key]['error_rate'].append(error_rate)
            category_total_stats_segment2[category_key]['half_correct'] += half_correct

# Print results
for key, stats in accuracy_stats.items():
    accuracy = stats['correct'] / stats['total'] if stats['total'] > 0 else 0
    print(f"Accuracy for {key}: {accuracy:.4f}\n")
print("\nTotal Accuracy Statistics:\n")
for key, stats in total_accuracy_stats.items():
    total_accuracy = stats['correct'] / stats['total'] if stats['total'] > 0 else 0
    print(f"Total Accuracy for {key}: {total_accuracy:.4f}\n")

print("\nSegment 2 Additional Statistics:\n")
for key, stats in segment2_additional_stats.items():
    avg_correct_rate = sum(stats['correct_rate']) / len(stats['correct_rate']) if stats['correct_rate'] else 0
    avg_error_rate = sum(stats['error_rate']) / len(stats['error_rate']) if stats['error_rate'] else 0
    half_correct_percentage = (stats['half_correct'] / len(stats['correct_rate'])) * 100 if stats['correct_rate'] else 0
    print(f"{key}: Average Correct Rate: {avg_correct_rate:.4f}, Average Error Rate: {avg_error_rate:.4f}, Half Correct Percentage: {half_correct_percentage:.2f}%\n")

print("\nCategory Total Statistics for Segment 2:\n")
for key, stats in category_total_stats_segment2.items():
    avg_correct_rate = sum(stats['correct_rate']) / len(stats['correct_rate']) if stats['correct_rate'] else 0
    avg_error_rate = sum(stats['error_rate']) / len(stats['error_rate']) if stats['error_rate'] else 0
    half_correct_percentage = (stats['half_correct'] / len(stats['correct_rate'])) * 100 if stats['correct_rate'] else 0
    print(f"{key}: Average Correct Rate: {avg_correct_rate:.4f}, Average Error Rate: {avg_error_rate:.4f}, Half Correct Percentage: {half_correct_percentage:.2f}%\n")
    