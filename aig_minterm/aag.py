class AAG:
    def __init__(self, file_lines):
        self.lines = file_lines
        self.header = [int(string) for string in self.lines[0].split()[1:] ]
        #TODO
        self.max_idx = self.header[0]
        self.num_inputs = self.header[1]
        self.num_latches = self.header[2]
        self.num_outputs = self.header[3]
        self.num_ands = self.header[4]
        self.num_lines = self.num_inputs + self.num_latches + self.num_outputs + self.num_ands

        self.start_ands = self.num_inputs + self.num_latches + self.num_outputs + 1
        self.gates = file_lines[self.start_ands: self.start_ands + self.num_ands]
        self.start_of_outputs = self.num_inputs + self.num_latches + 1

    @property
    def outputs(self):
        return [int(string) for string in self.lines[self.start_of_outputs:self.start_of_outputs 
            + self.num_outputs]]

    """
    get an new unused variable name
    NOTE: assumes you have called init_max_idx() with the proper init value
    ---returns---
    new_var: int, the new variable
    """
    def get_var_idx(self):
        self.max_idx += 1
        return self.max_idx

