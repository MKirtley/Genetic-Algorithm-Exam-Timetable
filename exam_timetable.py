import csv
from collections import namedtuple, Counter, defaultdict
import random
from copy import deepcopy


# Global Variables
# Hard Constraints
CLASSROOMS = ["P411", "P412", "P413", "P414", "P415", "P416", "P417", "P418", "P419", "P420"]
EXAM_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
EXAM_ROOM = namedtuple('classroom', 'room_name morning tutor_morning afternoon tutor_afternoon')


class Solution:
    """
    A class used to represent a soltuion.
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


def load_data():
    """
    Load in the units, tutors, and students + units. Append them to lists.
    :return: Three lists - units, tutors, and students
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


def generate_exam_room(units, tutors):
    """
    Selecting a random unit and tutor and placing them in a random classroom.
    """

    available_units = units.copy()

    # Select a random unit and tutor for the morning session
    morning_unit, morning_tutor = random.choice(available_units), random.choice(tutors)

    # Remove the morning unit from the list of available units
    available_units.remove(morning_unit)

    # Select a random unit and tutor for the morning session
    afternoon_unit, afternoon_tutor = random.choice(available_units), random.choice(tutors)

    # Select a random classroom.
    room_name = random.choice(CLASSROOMS)

    # Assign the values to EXAM_ROOM namedtuple.
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
    for individual in range(population_size):
        solution = Solution(dict())
        available_units = units.copy()

        # Generate a random exam schedule for each day.
        for day in EXAM_DAYS:
            exam_day = []
            random_num_classrooms = random.randint(2, len(CLASSROOMS))

            # To avoid classrooms being assigned without an available unit.
            if random_num_classrooms > len(available_units):
                random_num_classrooms = len(available_units)

            #For each day, assign a random morning and afternoon unit & tutor.
            for classroom in range(random_num_classrooms):

                # Break the loop if there are no more units left. 
                if len(available_units) == 0:
                    break
                exam_room = generate_exam_room(available_units, tutors)
                exam_day.append(exam_room)

                # Remove assigned units from available units to avoid units.
                if exam_room.morning in available_units:
                    available_units.remove(exam_room.morning)
                if exam_room.afternoon in available_units:
                    available_units.remove(exam_room.afternoon)

            # set the exam day to a day in the solution class.        
            solution.schedule[day] = exam_day

        # Append the schedule to the new population.
        new_population.append(solution)

    return new_population


def hard_constraint_all_units(solution, units):
    """
    Hard constraint.
    An exam will be scheduled for each unit.
    :return: The score of the constraint and valid.
    """
    valid = True
    exam_list = []

    # Storing all exams (units) that exist in a solution.
    for day in solution.schedule:
        class_list = solution.schedule[day]

        for _class in class_list:
            exam_list.append(_class.morning)
            exam_list.append(_class.afternoon)

    # Storing each unique unit code.
    exam_codes = set([unit for unit in units])

    # Number of missing exams in exam_list.
    missing = len(exam_codes.difference(exam_list))

    # Constraint violated if an exam isn't scheduled.
    if missing > 0:
        valid = False
    
    score = 1 / (1 + missing) * 10

    return score, valid


def hard_constraint_unit_count(unit_allocation):
    """
    Hard Constraint.
    A student is enrolled in at least one unit, but can be enrolled upto four units.
    :return: The score of the constraint and valid.
    """

    valid = True
    invalid_num_units = 0

    for student in unit_allocation:
        if len(student.units) < 1 and len(student.units) > 4:
            valid = False
            invalid_num_units += 1

    score = 1 / (1 + invalid_num_units) * 10

    return score, valid


def count_student_exams_new(solution, student, day):
    """
    Helper function.
    Counting the number of exams for each student on a given day.
    :return: count
    """
    # Listing all exams (units) in a day.
    exam_list = []
    for unit in solution.schedule[day]:
        exam_list.extend([unit.morning[0], unit.afternoon[0]])

    # Couting the number of exams assigned to the student.
    count = sum(1 for unit in [student.units] if unit in exam_list)

    return count


def count_student_exams(solution, student, day):
    """
    Helper function.
    Counting the number of exams for each student on a given day.
    :return: count
    """
    # Listing all exams (units) in a day.
    exam_list = []
    for unit in solution.schedule[day]:
        exam_list.extend([unit.morning[0], unit.afternoon[0]])

    # Couting the number of exams assigned to the student.
    exam_counts = Counter(exam_list)
    count = sum(1 for unit in student.units if exam_counts[unit] == 1)

    return count


def hard_constraint_exam_clash(solution, unit_allocation):
    """
    Hard constraint.
    A student cannot appear in more than one exam at a time.
    :return: Fitness score and valid.
    """

    valid = True

    # Storing the number of exams in a week.
    num_of_exams = defaultdict(int)

    # For each student in each unit on each day.
    for day in solution.schedule:
        for student in unit_allocation:
            # Count the number of exams for the student on the current day.
            num_of_exams[student.name] += count_student_exams(solution, student, day)

    timeslot_clashes = 0
    for name, count in num_of_exams.items():
        if count > 1:
            # Check if the student has multiple exams in the same morning time slot.
            if any(unit.morning in student.units for unit in solution.schedule[day]) and \
                    any(unit.morning in student.units for unit in solution.schedule[day]):

                # Add 1 to timeslot_clashes if true.
                timeslot_clashes += 1

            # Check if the student has multiple exams in the same afternoon time slot.
            elif any(unit.afternoon in student.units for unit in solution.schedule[day]) and \
                    any(unit.afternoon in student.units for unit in solution.schedule[day]):

                # Add 1 to timeslot_clashes if true.
                timeslot_clashes += 1

    # Invalid exam timetable if there's a timeslot clash.
    if timeslot_clashes > 0:
        valid = False

    score = 1 / (1 + timeslot_clashes) * 10

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
        unit_list = solution.schedule[day]
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

    # Add all exams (units) in the solution to exam_list
    for day in solution.schedule:
        unit_list = solution.schedule[day]
        for unit in unit_list:
            exam_list.extend([unit.morning, unit.afternoon])

    # Count the number of duplicates
    duplicate_count = dict(Counter(exam_list))
    duplicates = sum(1 for value in duplicate_count.values() if value > 1)

    # Invalid if there's a duplicate exam.
    if duplicates > 1:
        valid = False

    score = 1 / (1 + duplicates) * 10
    return score, valid

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
    for name, count in exam_count.items():
        if count > 1:
                # Add 1 to timeslot_clashes if true.
                consecutive_exams += 1

    # Invalid exam timetable if there's a timeslot clash.
    if consecutive_exams > 0:
        valid = False

    score = 1 / (1 + consecutive_exams) * 2

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
        unit_list = solution.schedule[day]
    
        # Store the assigned tutors in the morning and afternoon lists.
        for unit in unit_list:
            invigilator_list.extend([unit.tutor_morning, unit.tutor_afternoon])
        
        # Count the number of times each tutor is in the lists.
    invigilator_duty_count = Counter(invigilator_list)
    
    sum_of_duties = 0
    for duties in invigilator_duty_count.values():
       sum_of_duties += duties

    average = sum_of_duties / len(invigilator_duty_count)
    rounded_average = round(average, 2)

    if rounded_average != desired_average:
        valid = False
    
    absolute = abs(rounded_average - desired_average)
    score = 1 / (1 + absolute) * 2

    return score, valid


def constraints_check(solution, units, unit_allocation, tutors):
    """
    Checks if all hard and soft constraints are satisfied.
    :return: If true, the genetic algorithm will return the solution.
    """      
    au_score, all_units = hard_constraint_all_units(solution, units)
    uc_score, unit_count = hard_constraint_unit_count(unit_allocation)
    ec_score, exam_clash = hard_constraint_exam_clash(solution, unit_allocation)  
    de_score, duplicate_exams = hard_constraint_duplicate_exams(solution)
    tc_score, tutor_clash = hard_constraint_tutor_clash(solution)
    ce_score, consecutive_exams = soft_constraint_two_exams(solution, unit_allocation)
    ei_score, equal_invigilators = soft_constraint_invigilation_duties(solution, units, tutors)
    

    print(f"All Units: {all_units}, Duplicate Exams: {duplicate_exams}, Exam_Clash: {exam_clash}, Tutor Clash: {tutor_clash}, Unit Count: {unit_count}, Consecutive Exams: {consecutive_exams}, Equal Invigilators: {equal_invigilators}")

    if all_units and unit_count and exam_clash and duplicate_exams and tutor_clash and consecutive_exams and equal_invigilators:
        return True

    return False


def calculate_fitness(population, units, unit_allocation, tutors):
    """
    Calculate fitness score.
    """
    for solution in population:
        au_score, all_units = hard_constraint_all_units(solution, units)
        uc_score, unit_count = hard_constraint_unit_count(unit_allocation)
        de_score, duplicate_exams = hard_constraint_duplicate_exams(solution)
        ec_score, exam_clash = hard_constraint_exam_clash(solution, unit_allocation)
        tc_score, tutor_clash = hard_constraint_tutor_clash(solution)
        ce_score, consecutive_exams = soft_constraint_two_exams(solution, unit_allocation)
        ei_score, equal_invigilators = soft_constraint_invigilation_duties(solution, units, tutors)

        fitness = au_score + uc_score + de_score + ec_score + tc_score + ce_score + ei_score        
        solution.fitness = float(fitness)                             

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
    parents[2:] = random.choices(population, weights=[s.fitness for s in population], k=len(population))
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
        exams_list_a = parent_a.schedule[day]
        exams_list_b = parent_b.schedule[day]

        #Child1 gets the exam list before the crossover point from parent_a
        #The remaining exams are given from parent_b
        child1.schedule[day] = deepcopy(exams_list_a if i < crossover_point else exams_list_b)

        #Child 2 gets the opposite.
        child2.schedule[day] = deepcopy(exams_list_b if i < crossover_point else exams_list_a)

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

    # Generate population.
    population = [generate_population(population_size, units, tutors)]

    # For each generation.
    for i in range(max_generations):

        # Calculate the fitness of each solution.
        population_fitness = calculate_fitness(population[0], units, unit_allocation, tutors)

        # Selection and crossover.
        parents = selection(deepcopy(population_fitness))
        crossover_population = apply_crossover(parents, crossover_probability)
        calculate_fitness(crossover_population, units, unit_allocation, tutors)

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
        print(f"\nGeneration: {i+1}\tCurrent fitness: {best_solution.fitness}\tStagnant: {stagnant}")
        
        # Check if all hard_constrats are fulfilled.
        if constraints_check(best_solution, units, unit_allocation, tutors):
            print("All hard constraints satisfied")
            return best_solution
        
        # If stuck in local convergance, return the current best solution.
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
