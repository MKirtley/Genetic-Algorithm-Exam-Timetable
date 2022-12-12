import csv
from collections import namedtuple, Counter, defaultdict
import random
import numpy as np
from copy import deepcopy
import pandas as pd


# Global Variables
# Hard Constraints
CLASSROOMS = ["P411", "P412", "P413", "P414", "P415", "P416", "P417", "P418", "P419", "P420"]
EXAM_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
EXAM_ROOM = namedtuple('classroom', 'room_name morning tutor_morning afternoon tutor_afternoon')



class StudentData:
    def __init__(self, name, units):
        self.name = name
        self.units = []
        self.units.append(units)

    def add_unit(self, unit):
        self.units.append(unit)

    def __repr__(self):                                               
        output = "Name: " + self.name + "\t" + "Units: " + str(self.units) + "\n"
        return output


def add_student(student_list, name, cc):                               
    """
    Adding students and their units to StudentData.
    """
    for student in student_list:
        if student.name == name:
            if cc not in student.units:                              
                student.add_unit(cc)
            return

    new_student = StudentData(name, cc)
    student_list.append(new_student)


class Solution:
    def __init__(self, days=dict(), fitness=0):
        self.days = days
        self.fitness = fitness

        for day in EXAM_DAYS:
            self.days[day] = []
    
    def __str__(self):
        return "Best Solution: {}".format(self.days)


def is_course_in_list(units, code):
    """
    Helper function.
    Checking if unit already exists.
    """
    for unit in units:
        if code == unit[0]:
            return True

    return False


def load_data():
    """
    Load in the units, tutors, and students + units. Append them to lists.
    :return: Three lists - units, tutors, and students_units
    """

    units = []
    with open("units.csv.csv", "r") as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        for row in reader:
            code_title = row[0], row[1]

            if not is_course_in_list(units, code_title[0]):
                units.append(code_title)

    tutors = []
    with open("tutor.csv.csv", "r") as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        for row in reader:
            tutors.append(row[0])
    
    students = []
    with open("student_units.csv.csv", "r") as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        for row in reader:
            name = row[1]
            student_unit = row[2]
            add_student(students, name, student_unit)
    
    return units, tutors, students


def generate_exam_room(units, tutors):
    """
    Selecting a random unit and tutor and placing them in a random classroom.
    """
    # Select a random unit and tutor for the morning and afternoon sessions.
    morning_unit, morning_tutor = random.choice(units), random.choice(tutors)
    afternoon_unit, afternoon_tutor = random.choice(units), random.choice(tutors)

    # Select a random classroom.
    room_name = random.choice(CLASSROOMS)

    # Assign the values to EXAM_ROOM
    return EXAM_ROOM(
        room_name=room_name,
        morning=morning_unit,
        tutor_morning=morning_tutor,
        afternoon=afternoon_unit,
        tutor_afternoon=afternoon_tutor
    )

def generate_population(population_size, units, tutors):
    """
    Generate a random population that fulfils all the hard constraints.
    :return: A new population. 
    """
    new_population = []
    # Create a solution for each population.
    for i in range(population_size):
        solution = Solution(dict())
        # Generate a random exam schedule for each day.
        for day in EXAM_DAYS:
            available_units = units.copy()
            exam_schedule = []
            for j in range(random.randint(0, len(CLASSROOMS) -1)):
                exam_room = generate_exam_room(available_units, tutors)
                exam_schedule.append(exam_room)
                
                if exam_room.morning in available_units:
                    available_units.remove(exam_room.morning)
                if exam_room.afternoon in available_units:
                    available_units.remove(exam_room.afternoon)

            solution.days[day] = exam_schedule
        
        # Append the schedule to the new population.
        new_population.append(solution)

    return new_population


def hard_constraint_all_units(solution, units):
    """
    Hard constraint.
    An exam will be scheduled for each unit.
    Unit name and code are presented in units.csv file.
    :return: The score of the constraint and valid.
    """
    valid = True
    exam_list = []

    # Storing all exams (units) that exist in a solution.
    for day in solution.days:
        class_list = solution.days[day]

        for _class in class_list:
            exam_list.append(_class.morning)
            exam_list.append(_class.afternoon)

    # Storing each unique unit code.
    exam_codes = set([unit[0] for unit in units])

    # Number of missing exams in exam_list.
    missing = len(exam_codes.difference(exam_list))

    # Constraint violated if an exam isn't scheduled.
    if missing > 0:
        valid = False
    
    num = (1 / (1 + missing))

    return num, valid


def hard_constraint_unit_count(unit_allocation):
    """
    Hard Constraint.
    A student is enrolled in at least one unit, but can be enrolled upto four units.
    """
    for student in unit_allocation:
        if len(student.units) < 1 and len(student.units) > 4:
            return False

    return True


def count_student_exams(solution, student, day):
    """
    Helper function.
    Counting the number of exams for each student on a given day.
    :return: count
    """
    # Listing all exams (units) in a day.
    exam_list = []
    for unit in solution.days[day]:
        exam_list.extend([unit.morning[0], unit.afternoon[0]])

    # Couting the number of exams assigned to the student.
    exam_counts = Counter(exam_list)
    count = sum(1 for unit in student.units if exam_counts[unit] == 1)

    return count



def hard_constraint_exam_clash(solution, unit_allocation):
    """
    Hard constraint.
    A student cannot appear in more than one exam at a time.
    """

    valid = True
    # Storing the number of clashes in a day.
    student_clashes = defaultdict(int)

    # For each student in each unit on each day.
    for day in solution.days:
        for student in unit_allocation:

            # Count the number of exams for the student on the current day.
            student_clashes[student.name] += count_student_exams(solution, student, day)

    
    timeslot_clashes = 0
    for name, count in student_clashes.items():
        if count > 1:
            # Check if the student has multiple exams in the same morning time slot.
            if any(unit.morning in student.units for unit in solution.days[day]) and \
               any(unit.morning in student.units for unit in solution.days[day]):
                
                # Add 1 to timeslot_clashes if true.
                timeslot_clashes += 1

            # Check if the student has multiple exams in the same afternoon time slot.
            elif any(unit.afternoon in student.units for unit in solution.days[day]) and \
                 any(unit.afternoon in student.units for unit in solution.days[day]):
                
                # Add 1 to timeslot_clashes if true.
                timeslot_clashes += 1
    
    # Invalid exam timetable if there's a timeslot clash.
    if timeslot_clashes > 0:
        valid = False
    return 1 / (1 + timeslot_clashes), valid



def hard_constraint_tutor_clash(solution):
    """
    Hard constraint.
    A tutor can only invigilate one exam at a time.
    Counts the number of times a tutor invigilates an exam at each time slot.
    """
    # Counting the number of clashes.
    clashes = 0
    valid = True

    # Looping through each exam day.
    for day in solution.days:
        unit_list = solution.days[day]
        morning_list = []
        afternoon_list = []

        # Store the assigned tutors in the morning and afternoon lists.
        for unit in unit_list:
            morning_list.append(unit.tutor_morning)
            afternoon_list.append(unit.tutor_afternoon)
        
        # Count the number of times each tutor is in the lists.
        morning_duplicates = Counter(morning_list)
        afternoon_duplicates = Counter(afternoon_list)

        # Add 1 to clashes for any duplicates.
        for count in morning_duplicates.values():
            if count > 1:
                clashes += 1
        
        for count in afternoon_duplicates.values():
            if count > 1:
                clashes += 1

    # Invalid exam timetable if there's a clash.
    if clashes > 0:
        valid = False
    
    num = (1 / (1 + clashes))

    return num, valid


def hard_constraint_duplicate_exams(solution):
    """
    Not part of hard constraint list, but it stops duplicate exams.
    :return: The score of the constraint and valid.
    """
    exam_list = []
    valid = True

    # Add all exams (units) in the solution to exam_list
    for day in solution.days:
        unit_list = solution.days[day]
        for unit in unit_list:
            exam_list.extend([unit.morning, unit.afternoon])

    # Count the number of duplicates
    duplicate_count = dict(Counter(exam_list))
    duplicates = sum(1 for value in duplicate_count.values() if value > 1)

    # Invalid if there's a duplicate exam.
    if duplicates > 1:
        valid = False

    return 1 / (1 + duplicates), valid


def hard_constraints_check(solution, units, unit_allocation):
    """
    Checks if all hard constraints are satisfied
    """
    au_score, all_units = hard_constraint_all_units(solution, units)
    de_score, duplicate_exams = hard_constraint_duplicate_exams(solution)
    ec_score, exam_clash = hard_constraint_exam_clash(solution, unit_allocation)
    tc_score, tutor_clash = hard_constraint_tutor_clash(solution)
    unit_count = hard_constraint_unit_count(unit_allocation)

    if all_units and duplicate_exams and exam_clash and tutor_clash and unit_count:
        return True

    return False


def calculate_fitness(population, units, unit_allocation):
    """
    Calculate fitness score.
    """
    for solution in population:
        au_score, all_units = hard_constraint_all_units(solution, units)
        de_score, duplicate_exams = hard_constraint_duplicate_exams(solution)
        ec_score, exam_clash = hard_constraint_exam_clash(solution, unit_allocation)
        tc_score, tutor_clash = hard_constraint_tutor_clash(solution)

        fitness = au_score + de_score + ec_score + tc_score         
        solution.fitness = fitness                               

    return population


def get_fitness(solution):
    """
    Get the current fitness value from the solution.
    """
    return solution.fitness


def elitism(population):
    """
    Elitism - get the top two solutions with highest fitness values.
    :return: The two solutions with the highest fitness values.
    """
    population.sort(key=get_fitness, reverse=True)

    return population[0], population[1]


def selection(population):
    """
    Elitism and Roulette Wheel Selection
    :return: parents
    """
    #Appending the two solutions with the highest fitness values.
    parents = []    
    parents.extend(elitism(population))

    #The rest of the population are selected at random, with the higher fitness values having a greater chance of being selected.
    parents[2:] = random.choices(population, weights=[s.fitness for s in population], k=len(population) -2)
    return parents


def crossover(parent_a, parent_b):
    """
    Crossover. 
    Combining the genetic information from two parents into two children.
    :return: two children from 2 parents
    """

    #Setting a random crossover point in EXAM_DAYS and creating child variables.
    crossover_point = random.randint(1, len(EXAM_DAYS))
    child1 = Solution()
    child2 = deepcopy(child1)

    #For each exam day, get the exam list from both parents.
    for i, day in enumerate(EXAM_DAYS):
        exams_list_a = parent_a.days[day]
        exams_list_b = parent_b.days[day]

        #Child1 gets the exam list before the crossover point from parent_a
        #The remaining exams are given from parent_b
        child1.days[day] = deepcopy(exams_list_a if i < crossover_point else exams_list_b)

        #Child 2 gets the opposite.
        child2.days[day] = deepcopy(exams_list_b if i < crossover_point else exams_list_a)

    return child1, child2


def apply_crossover(population, crossover_probability):
    """
    Applies crossover dependant on the probability.
    :return: A new population.
    """

    crossovered_population = []

    for i in range(len(population)):
        if random.random() < crossover_probability:
            parent_a, parent_b = random.sample(population, 2)
            crossovered_population.extend(crossover(parent_a, parent_b))
    
    return crossovered_population



def genetic_algorithm(population_size, max_generations, crossover_probability, units, tutors, unit_allocation):
    """
    The genetic algorithm.
    :return: The best solution.
    """

    best_solution = None
    previous_best = None
    stagnant = 50
    reset_count = 0

    # Generate population.
    population = [generate_population(population_size, units, tutors)]

    # For each generation.
    for i in range(max_generations):

        # Calculate the fitness of each solution.
        population_fitness = calculate_fitness(population[0], units, unit_allocation)

        # Selection and crossover.
        parents = selection(deepcopy(population_fitness))
        crossover_population = apply_crossover(parents, crossover_probability)
        calculate_fitness(crossover_population, units, unit_allocation)

        # Get solution with highest fitness and assign it as best_solution.
        solution1, _ = elitism(crossover_population)
        if best_solution is None:
            stagnant = 0
            best_solution = deepcopy(solution1)
        
        # Replace if a better solution is found.
        elif solution1.fitness > best_solution.fitness:
            stagnant = 0
            best_solution = deepcopy(solution1)
        
        # Add 1 to stagnant if there's no improvement to fitness.
        if best_solution.fitness == previous_best:
            stagnant += 1
        
        # Set the current solution to pthe previous best to check stagnation 
        previous_best = deepcopy(best_solution.fitness)
        print(f"Generation: {i+1} Current fitness: {best_solution.fitness} Stagnant: {stagnant}")
        
        # Check if all hard_constrats are fulfilled.
        if hard_constraints_check(best_solution, units, unit_allocation):
            print("All hard constraints satisfied")
            return best_solution
        
        # If stuck in local convergance, return the current best.
        if stagnant == 50:
            print("Unable to optimise further. Returning best solution.")
            best, _ = elitism(crossover_population)
            return best
    
        else:
            population.clear()
            population.append(crossover_population)

    return best_solution


def main():
    """
    Main function.
    Control parameter settings.
    Runs the evolutionary algorithm sequence.
    :return: None
    """

    unit_list, tutor_list, student_units = load_data()


    population_size = 50
    max_generations = 10
    crossover_prob = 1
    #mutation_prob = 0.1

    solution = genetic_algorithm(population_size, max_generations, crossover_prob, unit_list, tutor_list, student_units)

    print(solution)



if __name__ == "__main__":
    print("Start")
    main()
    print("End")