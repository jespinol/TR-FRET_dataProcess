import csv
import tkinter as tk


class Grid:
    def __init__(self, m, n):
        self.m = m
        self.n = n
        self.sets = []
        self.cells = [[0 for _ in range(n)] for _ in range(m)]  # 0 represents an unpopulated cell

    def add_set(self, set):
        self.sets.append(set)

    def display_sets(self):
        for set in self.sets:
            print(f"Set: {set.control1}, {set.control2}")

    # def populate_from_csv(self, file_path):
    #     with open(file_path, 'r') as f:
    #         reader = csv.reader(f)
    #         for i, row in enumerate(reader):
    #             # print(row)
    #             for j, cell in enumerate(row):
    #                 self.cells[i][j] = 1
    def populate_from_csv(self, file_path):
        with open(file_path, 'r') as f:
            reader = csv.reader(f)
            for i, row in enumerate(reader):
                # If the row is empty or contains only whitespace, stop reading
                print(f"row {row}")
                if not row or all(cell.isspace() or cell == '' for cell in row):
                    print("end of row?")
                    break
                # elif :
                #     print("empty row")
                #     break
                for j, cell in enumerate(row):
                    self.cells[i][j] = 1


class Set:
    def __init__(self, control1, control2):
        self.control1 = control1
        self.control2 = control2
        self.xmin = min(control1[0], control2[0])
        self.ymin = min(control1[1], control2[1])
        self.xmax = max(control1[0], control2[0])
        self.ymax = max(control1[1], control2[1])


class GridGUI:
    def __init__(self, grid):
        self.root = tk.Tk()
        self.grid = grid
        self.buttons = [[None for _ in range(grid.n)] for _ in range(grid.m)]
        self.control1 = None
        self.control2 = None
        for i in range(grid.m):
            for j in range(grid.n):
                text = 'X' if grid.cells[i][j] == 1 else ' '
                self.buttons[i][j] = tk.Button(self.root, text=text,
                                               command=lambda i=i, j=j: self.select_point(i, j))
                self.buttons[i][j].grid(row=i, column=j)

    def select_point(self, i, j):
        if not self.control1:
            self.control1 = (i, j)
            self.buttons[i][j].config(text='C1')
        elif not self.control2:
            self.control2 = (i, j)
            self.buttons[i][j].config(text='C2')
            self.create_set()
        else:
            print("Two controls already selected. Resetting.")
            self.reset_controls()

    def reset_controls(self):
        if self.control1:
            i, j = self.control1
            self.buttons[i][j].config(text='P' if self.grid.cells[i][j] == 1 else ' ')
        if self.control2:
            i, j = self.control2
            self.buttons[i][j].config(text='P' if self.grid.cells[i][j] == 1 else ' ')
        self.control1 = None
        self.control2 = None

    def create_set(self):
        set = Set(self.control1, self.control2)
        self.grid.add_set(set)
        print(f"Set created: {set.control1}, {set.control2}")
        self.reset_controls()

    def run(self):
        self.root.mainloop()


# Create the grid and run the GUI
grid = Grid(16, 24)
grid.populate_from_csv('/Users/jespinol/Downloads/TR-FRET/gui/c.csv')  # read grid cells from csv
GridGUI(grid).run()
