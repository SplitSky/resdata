class Tree(object):
    def __init__(self, nodes):
    # data is a list[dict["project_name" : "", "experiment_data" : dict[{"experiment_name" : dataset_names_list}] ]]
        self.tree = {}
        self.node_names = set()
        
        if nodes != None:
            self.insert_node("root", None)
            for proj_dict in nodes:
                self.insert_node(proj_dict.get("project_id"), "root")
                for exp_dict in proj_dict.get("experiment_list"):
                    self.insert_node(exp_dict.get("experiment_id"),proj_dict.get("project_id"))
                    for dataset_name in exp_dict.get("dataset_list"):
                        self.insert_node(dataset_name, exp_dict.get("experiment_name"))

    def insert_node(self, node_name, parent_name):
        parent_node = self.tree.get(parent_name)
        if parent_node is None:
            parent_node = {}
            self.tree[parent_name] = parent_node
        node = parent_node.get(node_name)
        if node is None:
            node = {}
            parent_node[node_name] = node
            self.node_names.add(node_name)

    def check_node_exists(self, node_name):
        return node_name in self.node_names

    def clear_tree(self):
        self.tree = {}
        self.node_names = set()

    def delete_node(self, node_name):
        if node_name not in self.node_names:
            return True
        del self.tree[node_name]
        self.node_names.remove(node_name)
        for parent_name, parent_node, in self.tree.items():
            if node_name in parent_node:
                del parent_node[node_name]
                break

