"""
Exam timetable generator.
Inspired, altered and improved from HxnDev's example: https://github.com/HxnDev/Exam-Scheduler-Generator-Using-Genetic-Algorithm
"""

import csv
import random
from math import ceil
from collections import Counter, defaultdict
from copy import deepcopy


# Global Variables
CLASSROOMS = ["P411", "P412", "P413", "P414", "P415", "P416", "P417", "P418", "P419", "P420"]
EXAM_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]


class Solution:
    """
    A class used to represent a solution.
    """
    def __init__(self, fitness=0):
        self.schedule = {day: [] for day in EXAM_DAYS}
        self.fitness = fitness
    
    def __str__(self):
        return "Best Solution: {}".format(self.schedule)


class StudentData:
    """
    A class used to represent a student and their units.
    """
    def __init__(self, name, units=None):
        self.name = name
        if units is None:
            self.units = []
        else:
            self.units = units

    def add_unit(self, unit):
        self.units.append(unit)

    def __repr__(self):                                               
        output = f"Name: {self.name}\tUnits: {self.units}\n"
        return output


class ExamRoom:
    """
    A class used to represent an exam room and its properties.
    """
    def __init__(self, room_name, morning_unit, morning_invigilator, afternoon_unit, afternoon_invigilator):
        self.room_name = room_name
        self.morning_unit = morning_unit
        self.morning_invigilator = morning_invigilator
        self.afternoon_unit = afternoon_unit
        self.afternoon_invigilator = afternoon_invigilator
    
    def __repr__(self):
        output = f"Room Name: {self.room_name}, Morning Unit: {self.morning_unit}, Morning Invigilator: {self.morning_invigilator}, Afternoon Unit: {self.afternoon_unit}, Afternoon Invigilator: {self.afternoon_invigilator}"
        return output
    

def load_data():
    """
    Load in the units, tutors, and students + units. Append them to lists.
    :return: Three lists - units, tutors, and students + units.
    """
    # Load in units.
    units = []
    with open("units.csv.csv", "r") as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        for row in reader:
            code_title = row[0], row[1]
            units.append(code_title)

    # Load in tutors.
    tutors = []
    with open("tutor.csv.csv", "r") as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        for row in reader:
            tutors.append(row[0])
    
    # Load in student + units.
    student_units = []
    with open("student_units.csv.csv", "r") as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        for row in reader:
            new_student = StudentData(row[1], row[2])
            student_units.append(new_student)
    
    return units, tutors, student_units


def generate_exam_room(units, tutors, classroom):
    """
    Selecting a random morning & afternoon units and tutors and creating an exam room.
    :return: ExamRoom object.
    """

    available_units = units.copy()

    # Select a random unit and tutor for the morning session
    morning_unit, morning_tutor = random.choice(available_units), random.choice(tutors)

    # Remove the morning unit from the list of available units
    available_units.remove(morning_unit)

    # Select a random unit and tutor for the morning session
    afternoon_unit, afternoon_tutor = random.choice(available_units), random.choice(tutors)

    # Exam room object.
    exam_room = ExamRoom(room_name=classroom, 
        morning_unit=morning_unit, 
        morning_invigilator=morning_tutor, 
        afternoon_unit=afternoon_unit, 
        afternoon_invigilator=afternoon_tutor)
    
    return exam_room


def generate_population(population_size, units, tutors):
    """
    Generate a random population.
    Ensures all units are given a room and invigilator and set as an exam.
    :return: A new population. 
    """
    new_population = []

    # Create a solution for each population.
    for individual in range(population_size):
        solution = Solution()
        available_units = units.copy()

        # Generate a random exam schedule for each day.
        for day in EXAM_DAYS:
            exam_day = []

            # Setting a random number of classrooms
            random_num_classrooms = random.randint(2, len(CLASSROOMS))

            # To avoid classrooms being assigned without an available unit.
            if random_num_classrooms > len(available_units):
                random_num_classrooms = len(available_units)
            
            # To avoid multiple exams falling into the same classroom at the same time.
            available_classrooms = random.choices(CLASSROOMS, k=random_num_classrooms)

            #For each day, assign a random morning and afternoon unit & tutor.
            for classroom in available_classrooms:

                # Break the loop if there are no more units left. 
                if len(available_units) == 0:
                    break
                exam_room = generate_exam_room(available_units, tutors, classroom)
                exam_day.append(exam_room)

                # Remove assigned units from available units to avoid duplications.
                if exam_room.morning_unit in available_units:
                    available_units.remove(exam_room.morning_unit)
                if exam_room.afternoon_unit in available_units:
                    available_units.remove(exam_room.afternoon_unit)

            # Set the exam day to a day in the solution class.        
            solution.schedule[day] = exam_day

        # Append the schedule to the new population.
        new_population.append(solution)

    return new_population


def hard_constraint_all_units(solution, units):
    """
    Hard constraint.
    An exam will be scheduled for each unit.
    Counting the number of missing units.
    :return: The score of the constraint and valid.
    """
    valid = True
    exam_list = set()

    # Storing all exams (units) that exist in a solution.
    for day in solution.schedule:
        room_list = solution.schedule[day]

        for room in room_list:
            exam_list.update([room.morning_unit, room.afternoon_unit])

    # Number of missing exams in exam_list.
    missing = len(units) - len(exam_list)

    # Constraint violated if an exam isn't scheduled.
    if missing > 0:
        valid = False
        score = round((1 / (1 + missing) * 10) / 2, 2)
    else:
        score = round((1 / (1 + missing) * 10), 2)
    
    return score, valid


def hard_constraint_unit_count(unit_allocation):
    """
    Hard Constraint.
    A student is enrolled in at least one unit, but can be enrolled in up to four units.
    :return: The score of the constraint and valid.
    """

    valid = True
    invalid_num_units = 0

    # Iterating through students and checking the number of units.
    for student in unit_allocation:
        if 1 > len(student.units) > 4:
            valid = False
            invalid_num_units += 1

    if not valid:
        score = round((1 / (1 + invalid_num_units) * 10) / 2, 2)
    else:
        score = round((1 / (1 + invalid_num_units) * 10), 2)

    return score, valid


def hard_constraint_exam_clash(solution, unit_allocation):
    """
    Hard constraint.
    A student cannot appear in more than one exam at a time.
    :return: Fitness score and valid.
    """
    valid = True
    timeslot_clashes = 0

    # Iterating through each day and room
    exam_counts = Counter()
    for day in solution.schedule:
        room_list = solution.schedule[day]

        for room in room_list:

            # Iterating through each student and counting the number of exams they have at a given timeslot.
            for student in unit_allocation:
                if room.morning_unit[0] in student.units:
                    exam_counts[(student.name, "morning")] += 1
                if room.afternoon_unit[0] in student.units:
                    exam_counts[(student.name, "afternoon")] += 1

    # More than 1 would indicate a timeslot clash.
    for count in exam_counts.values():
        if count > 1:
            timeslot_clashes += 1
            valid = False

    if not valid:
        score = round((1 / (1 + timeslot_clashes) * 10) / 2, 2)
    else:
        score = round((1 / (1 + timeslot_clashes) * 10), 2)

    return score, valid


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
    for day in solution.schedule:
        room_list = solution.schedule[day]
        morning_list = []
        afternoon_list = []

        # Store the assigned tutors in the morning and afternoon lists.
        for room in room_list:
            morning_list.append(room.morning_invigilator)
            afternoon_list.append(room.afternoon_invigilator)
        
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
    
    if not valid:
        score = round((1 / (1 + clashes) * 10) / 2, 2)
    else:
        score = (1 / (1 + clashes) * 10)

    return score, valid


def hard_constraint_duplicate_exams(solution):
    """
    Hard constraint.
    Not part of hard constraint list, but it counts duplicate exams.
    :return: The score of the constraint and valid.
    """
    exam_list = []
    valid = True

    # Add all exams in the solution to exam_list
    for day in solution.schedule:
        room_list = solution.schedule[day]

        for room in room_list:
            exam_list.extend([room.morning_unit, room.afternoon_unit])

    # Count the number of duplicates
    duplicate_count = dict(Counter(exam_list))
    duplicates = sum(1 for value in duplicate_count.values() if value > 1)

    # Invalid if there's a duplicate exam.
    if duplicates > 1:
        valid = False

    if not valid:
        score = round((1 / (1 + duplicates) * 10) / 2, 2)
    else:
        score = round((1 / (1 + duplicates) * 10), 2)

    return score, valid


def count_student_exams(solution, student, day):
    """
    Helper function.
    Counting the number of exams for each student on a given day.
    :return: count
    """
    # Listing all exams in a day.
    exam_list = []
    for room in solution.schedule[day]:
        exam_list.extend([room.morning_unit[0], room.afternoon_unit[0]])

    # Counting the number of exams assigned to the student.
    count = sum(1 for exam in [student.units] if exam in exam_list)

    return count


def soft_constraint_two_exams(solution, unit_allocation):
    """
    Soft constraint.
    A Student should not sit in more than one exam consecutively in a day. 
    :return: Fitness score and valid.
    """

    valid = True

    # Storing the number of clashes in a day.
    exam_count = defaultdict(int)

    # For each student in each unit on each day.
    for day in solution.schedule:
        for student in unit_allocation:
            # Count the number of exams for the student on the current day.
            exam_count[student.name] += count_student_exams(solution, student, day)

    consecutive_exams = 0

    for count in exam_count.values():
        if count > 1:
                # Add 1 to timeslot_clashes if true.
                consecutive_exams += 1

    # Invalid exam timetable if there's a timeslot clash.
    if consecutive_exams > 0:
        valid = False

    if not valid:
        score = round((1 / (1 + consecutive_exams) * 5) / 2, 2)
    else:
        score = round((1 / (1 + consecutive_exams)) * 5, 2)

    return score, valid


def soft_constraint_invigilation_duties(solution, units, tutors):
    """
    Soft constraint.
    Tutors should have an equal number of invigilation duties.
    """
    # Counting the number of clashes.
    invigilator_list = []
    desired_average = round(len(units) / len(tutors), 2)
    valid = True

    # Looping through each exam day.
    for day in solution.schedule:
        room_list = solution.schedule[day]
    
        # Store the assigned invigilators in the list.
        for room in room_list:
            invigilator_list.extend([room.morning_invigilator, room.afternoon_invigilator])
        
    # Count the number of times each tutor is in the lists.
    invigilator_duty_count = Counter(invigilator_list)
    
    sum_of_duties = 0
    for duties in invigilator_duty_count.values():
       sum_of_duties += duties

    # Crossover has a chance to delete all exam rooms, this is to prevent a divide by zero error.
    if len(invigilator_duty_count) == 0:
        average = 100
    else:
        average = sum_of_duties / len(invigilator_duty_count)
    
    rounded_average = round(average, 2)

    if rounded_average != desired_average:
        valid = False
    
    absolute = abs(rounded_average - desired_average)

    if not valid:
        score = round((1 / (1 + absolute) * 5) / 2, 2)
    else:
        score = round((1 / (1 + absolute * 5)), 2)

    return score, valid



def get_fitness(solution):
    """
    Get the current fitness value from the solution.
    """
    return solution.fitness


def elitism(population):
    """
    Elitism - get the top two solutions with the highest fitness values.
    :return: The two solutions with the highest fitness values.
    """
    population.sort(key=get_fitness, reverse=True)

    return population[0], population[1]


def selection(population):
    """
    Elitism and Roulette Wheel Selection.
    Selecting parents with a length of half the population.
    :return: parents
    """
    #Appending the two solutions with the highest fitness values.
    parents = []    
    parents.extend(elitism(population))

    #The rest of the population are selected at random, with the higher fitness values having a greater chance of being selected.
    parents[2:] = random.choices(population, weights=[s.fitness for s in population], k=ceil(len(population) / 2 - 2))
    return parents


def crossover(parent_a, parent_b):
    """
    Crossover. 
    Combining the genetic information from two parents into two children.
    :return: Two children.
    """

    # Setting a random crossover point in EXAM_DAYS and creating child variables.
    crossover_point = random.randint(1, len(EXAM_DAYS))
    child_a = Solution()
    child_b = deepcopy(child_a)

    # For each exam day, get the exam list from both parents.
    for i, day in enumerate(EXAM_DAYS):
        exams_list_a = parent_a.schedule[day]
        exams_list_b = parent_b.schedule[day]

        # Child_a gets the exam list before the crossover point from parent_a
        # The remaining exams are given from parent_b
        child_a.schedule[day] = deepcopy(exams_list_a if i < crossover_point else exams_list_b)

        # Child_b gets the opposite.
        child_b.schedule[day] = deepcopy(exams_list_b if i < crossover_point else exams_list_a)

    return child_a, child_b


def apply_crossover(population, crossover_probability):
    """
    Applies crossover to two random solutions dependent on the probability.
    :return: A new population.
    """
    crossover_population = []

    # Select two random solutions and either apply crossover, or add them to new population.
    for i in range(len(population)):
        if random.random() < crossover_probability:
            parent_a, parent_b = random.sample(population, 2)
            crossover_population.extend(crossover(parent_a, parent_b))
        else:
            solution_a, solution_b = random.sample(population, 2)
            crossover_population.extend([solution_a, solution_b])
    
    return crossover_population


def mutation(solution, mutation_probability, tutors):
    """
    Mutation. 
    Randomly changing the genetic information of a solution.
    A random chance to alter the following:
        The day of an exam. - To alter the number of student and tutor clashes.
        The room of the exam. - To alter the distribution of assigned rooms.
        The exam's invigilator. - To reduce the invigilator clashes and average duties.
    :return: A mutated solution.
    """

    # Create an empty mutated copy
    mutated_solution = deepcopy(solution)
    for day in mutated_solution.schedule:
        room_list = mutated_solution.schedule[day]
        room_list.clear()

    # A random chance to change an exam room to another random day of the week.
    for day in solution.schedule:
        room_list = solution.schedule[day]
        possible_days = [d for d in EXAM_DAYS if d != day]
        for room in room_list:
            if random.random() < mutation_probability:
                new_day = random.choice(possible_days)
                mutated_solution.schedule[new_day].append(room)
            else:
                mutated_solution.schedule[day].append(room)

    # Change the room to another random room.
    for day in mutated_solution.schedule:
        room_list = mutated_solution.schedule[day]
        for room in room_list:
            if random.random() < mutation_probability:
                room.room_name = random.choice(CLASSROOMS)

    # Change the exam invigilators of each day to another.
    for day in mutated_solution.schedule:
        room_list = mutated_solution.schedule[day]
        for room in room_list:
            if random.random() < mutation_probability:
                room.morning_invigilator = random.choice(tutors)
                room.afternoon_invigilator = random.choice(tutors)

    return mutated_solution


def apply_mutation(population, mutation_probability, tutors):
    """
    Mutation.
    Applies mutation dependent on the probability.
    :return: A new population
    """
    mutated_population = []

    # Each solution has a chance of mutating
    for solution in population:
        if random.random() < mutation_probability:
            mutated_solution = mutation(solution, mutation_probability, tutors)
            mutated_population.append(mutated_solution)
        else:
            mutated_population.append(solution)

    return mutated_population


def constraints_check(solution, units, unit_allocation, tutors):
    """
    Checks if all hard and soft constraints are satisfied.
    :return: If true, the genetic algorithm will return the solution.
    """      
    au_score, all_units = hard_constraint_all_units(solution, units)
    de_score, duplicate_exams = hard_constraint_duplicate_exams(solution)
    ec_score, exam_clash = hard_constraint_exam_clash(solution, unit_allocation)
    tc_score, tutor_clash = hard_constraint_tutor_clash(solution)
    uc_score, unit_count = hard_constraint_unit_count(unit_allocation)  

    ce_score, consecutive_exams = soft_constraint_two_exams(solution, unit_allocation)
    ei_score, equal_invigilators = soft_constraint_invigilation_duties(solution, units, tutors)
    

    print(f"All Units: {all_units}, Duplicate Exams: {duplicate_exams}, Exam Clash: {exam_clash}, Tutor Clash: {tutor_clash}, Unit Count: {unit_count}, Consecutive Exams: {consecutive_exams}, Equal Invigilators: {equal_invigilators}")
    print(f"All Units: {au_score}, Duplicate Exams: {de_score}, Exam Clash: {ec_score}, Tutor Clash: {tc_score}, Unit Count: {uc_score}, Consecutive Exams: {ce_score}, Equal Invigilators: {ei_score}")

    if all_units and unit_count and exam_clash and duplicate_exams and tutor_clash and consecutive_exams and equal_invigilators:
        return True

    return False


def calculate_fitness(population, units, unit_allocation, tutors):
    """
    Calculate fitness score for each solution in the population.
    """
    for solution in population:
        au_score, all_units = hard_constraint_all_units(solution, units)
        de_score, duplicate_exams = hard_constraint_duplicate_exams(solution)
        ec_score, exam_clash = hard_constraint_exam_clash(solution, unit_allocation)
        tc_score, tutor_clash = hard_constraint_tutor_clash(solution)
        uc_score, unit_count = hard_constraint_unit_count(unit_allocation)

        ce_score, consecutive_exams = soft_constraint_two_exams(solution, unit_allocation)
        ei_score, equal_invigilators = soft_constraint_invigilation_duties(solution, units, tutors)

        fitness = au_score + de_score + ec_score + tc_score + uc_score + ce_score + ei_score        
        solution.fitness = fitness                           

    return population


def genetic_algorithm(population_size, max_generations, crossover_probability, mutation_probability, units, tutors, unit_allocation):
    """
    The genetic algorithm.
    Generates a random population. 
    Checks fitness.
    Applies selection, crossover, and mutation.
    Checks fitness and replaces the old population.
    :return: The best solution.
    """

    best_solution = None
    previous_best = None
    stagnant = 0

    # Generate population.
    population = [generate_population(population_size, units, tutors)]

    # For each generation.
    for i in range(max_generations):

        # Calculate the fitness of each solution.
        population_fitness = calculate_fitness(population[0], units, unit_allocation, tutors)

        # Selection
        parents = selection(population_fitness)

        # Crossover
        crossover_population = apply_crossover(parents, crossover_probability)
        crossover_fitness = calculate_fitness(crossover_population, units, unit_allocation, tutors)

        # Mutation
        mutated_population = apply_mutation(crossover_fitness, mutation_probability, tutors)
        mutated_fitness = calculate_fitness(mutated_population, units, unit_allocation, tutors)

        # Get the solution with the highest fitness and assign it as best_solution.
        solution1, _ = elitism(mutated_fitness)
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
        
        # Set the current solution to the previous best to check stagnation 
        previous_best = deepcopy(best_solution.fitness)
        print(f"\nGeneration: {i+1}\t Current best fitness: {best_solution.fitness}\t Stagnant: {stagnant}")
        
        # Check if all hard and soft constraints are fulfilled and return optimal solution if so.
        if constraints_check(best_solution, units, unit_allocation, tutors):
            print("All hard constraints satisfied")
            return best_solution

        # If not then replace population.
        else:
            population.clear()
            population.append(mutated_fitness)

    return best_solution


def main():
    """
    Main function.
    Control parameter settings.
    Runs the evolutionary algorithm sequence.
    :return: None
    """
    # Load the data.
    unit_list, tutor_list, student_units = load_data()

    # Set parameters.
    population_size = 100
    max_generations = 50
    crossover_prob = 1
    mutation_prob = 0.7

    # Generate Solution.
    solution = genetic_algorithm(population_size, max_generations, crossover_prob, mutation_prob, unit_list, tutor_list, student_units)

    # Print Results.
    print(solution)
    print(f"\nPopulation Size: {population_size}\nMax Generations: {max_generations}\nCrossover Probability: {crossover_prob}\nMutation Probability: {mutation_prob}")


if __name__ == "__main__":
    main()
