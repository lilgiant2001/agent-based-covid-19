import random
import copy
import CovidAgents
from spaces import Dorm, Academic, DiningHall, Gym, Library, SocialSpace, OffCampus, Office
from global_constants import DORM_BUILDINGS, ACADEMIC_BUILDINGS, PROBABILITY_G, PROBABILITY_S, PROBABILITY_L, \
    SCHEDULE_DAYS, SCHEDULE_WEEKDAYS, CLASS_TIMES, CLASSROOMS

def create_spaces(space, num_hours = 15, division = None):
    result = [[[] for j in range(num_hours)] for i in range(3)]
    all_methods = globals().copy()
    space_class = all_methods.get(space)
    for i in range(3):
        for j in range(num_hours):
            day = 'W'
            if i % 3 == 0:
                day = 'A'
            elif i % 3 == 1:
                day = 'B'
            if division is None:
                result[i % 3][j % num_hours] = space_class(day, j)
            else:
                result[i % 3][j % num_hours] = space_class(division, day, j)
    return result

def assign_meal(agent, day, start_hour, end_hour, dhArr):
    day_index = 0
    if day == 'B':
        day_index = 1
    elif day == 'W':
        day_index = 2
    possibleMealHours = agent.get_available_hours(start_hour, end_hour, day)
    if possibleMealHours:
        mealHour = random.choice(possibleMealHours)
        dhArr[day_index][mealHour].assign_agent(agent)

# initialize agents - list of agents
agent_list = CovidAgents.Agent().initialize()  # list of all agents


# agent_list = CovidAgents.Agent().initialize()  # initialize agents - list of all agents
# initializeLeaves(agent_list)


##############################################################################################################################
doubles_students = []
temp_doubles_dorm_times = [[[] for j in range(15)] for i in range(3)]
doubles_dorm_times = [[[] for j in range(15)] for i in range(3)]

def assign_dorms(dorms, on_campus_students):
    # list of available dorms that are not fully occupied
    available_dorms = copy.copy(dorms)

    # randomly assigns agents(on-campus students) to dorms
    for agent in on_campus_students:
        if len(dorms) == 0:  # if there are no available dorms (all dorms are full)
            print("All dorms are fully occupied")
        else:
            agent.dorm_building = random.choice(available_dorms)
            agent.dorm_room = agent.dorm_building.assign_agent(agent)
            if agent.dorm_room in agent.dorm_building.doubles:
                doubles_students.append(agent)
            if agent.dorm_building.status == "Full":
                available_dorms.remove(agent.dorm_building)
            # print(agent.dorm_building)
            # print(agent.dorm_room)


# prints all the agents in each dorm
# for dorm in dorms:
#   print(dorm.size + str(dorms.index(dorm) + 1))
#  dorm.returnAgents()

# CLASS ASSIGNMENT ------------------------------------------------------------------------------------------------------------------------------------
def assign_faculty_classes(day_time, academic_buildings, faculty_by_major):
    # dictionary of number of available classrooms for each timeslot for each major
    stem_available_timeslots = {}  # {'A2': 49, 'A4': 49, 'A6': 49, 'A8': 49, 'B2': 49, 'B4': 49, 'B6': 49, 'B8': 49}
    humanities_available_timeslots = {}  # {'A2': 24, 'A4': 24, 'A6': 24, 'A8': 24, 'B2': 24, 'B4': 24, 'B6': 24, 'B8': 24}
    arts_available_timeslots = {}  # {'A2': 22, 'A4': 22, 'A6': 22, 'A8': 22, 'B2': 22, 'B4': 22, 'B6': 22, 'B8': 22}
    available_timeslots = [stem_available_timeslots, humanities_available_timeslots, arts_available_timeslots]
    for major in available_timeslots:
        major_index = available_timeslots.index(major)

        if major_index == 0:
            major_timeslots = "STEM"
        elif major_index == 1:
            major_timeslots = "Humanities"
        else:  # if major_index == 2
            major_timeslots = "Arts"

        # list of the number of small/medium/large buildings for each major
        num_of_buildings = ACADEMIC_BUILDINGS.get(major_timeslots)
        # total number of classrooms for each major
        num_of_classrooms = num_of_buildings[0] * sum(CLASSROOMS.get("Small")) + num_of_buildings[1] * sum(
            CLASSROOMS.get("Medium")) + num_of_buildings[2] * sum(CLASSROOMS.get("Large"))

        for dt in day_time:
            available_timeslots[major_index].update({dt[0] + str(dt[1]): num_of_classrooms})

    # assign faculty to two timeslots until there are no more timeslots in the agent's major
    remaining_faculty = []  # list of faculty who can't get a class of their major (because the major classrooms are out of space)

    for major in available_timeslots:
        num_of_classrooms = list(major.values())[
            0]  # number of classrooms for every timeslot (they're all the same for same majors)
        major_index = available_timeslots.index(major)
        major_faculty = copy.copy(faculty_by_major[major_index])
        major_timeslots = available_timeslots[major_index]

        for i in range(num_of_classrooms):
            class_day_time = copy.copy(day_time)

            if len(major_faculty) < 4:
                four_faculty = copy.copy(major_faculty)
            else:
                four_faculty = random.sample(major_faculty, k=4)

            for faculty in four_faculty:
                two_classes = random.sample(class_day_time, k=2)
                for classes in two_classes:
                    class_day_time.remove(classes)
                    timeslot = classes[0] + str(classes[1])
                    major_timeslots[timeslot] -= 1
                    faculty.class_times.append([classes,
                                                major_index])  # appending [[day, time], major] of classroom because there will be agents who are assigned to classes that are not of their major

                major_faculty.remove(faculty)

        for faculty in major_faculty:
            remaining_faculty.append(faculty)
    # print(available_timeslots)

    remaining_majors = copy.copy(available_timeslots)  # list of major buildings that still have available timeslots
    for major in remaining_majors:
        if all(elem == 0 for elem in major.values()):
            remaining_majors.remove(major)
    random.shuffle(remaining_majors)

    # assign remaining faculty to timeslots of different majors that have available timeslots
    for major in remaining_majors:
        major_index = remaining_majors.index(major)
        major_timeslots = remaining_majors[major_index]

        for i in range(max(major.values())):
            available_times = []  # list of available timeslots in the major building
            for time in major.keys():
                if major.get(time) != 0:
                    available_times.append(time)

            if len(remaining_faculty) < (len(available_times) // 2):
                other_major_faculty = copy.copy(remaining_faculty)
            else:
                other_major_faculty = random.sample(remaining_faculty, k=(len(available_times) // 2))

            for faculty in other_major_faculty:

                two_timeslots = random.sample(available_times, k=2)
                for timeslot in two_timeslots:
                    available_times.remove(timeslot)
                    faculty.class_times.append([[timeslot[0], int(timeslot[1])], available_timeslots.index(
                        major)])  # appending [[day, time], major] of classroom
                    major_timeslots[timeslot] -= 1

                remaining_faculty.remove(faculty)
    # print(available_timeslots)

    # now assign all faculty to classes of corresponding major and [day, time]
    for major in academic_buildings:
        for day in major:
            for time in day:

                major_index = academic_buildings.index(major)
                day_index = major.index(day)
                if day_index == 0:
                    class_day = "A"
                else:  # day_index == 1:
                    class_day = "B"
                time_index = (day.index(time) + 1) * 2

                class_faculty = []
                # for faculty in faculty_list:
                #   if faculty.class_times[0] == [[class_day, time_index], major_index] or faculty.class_times[1] == [[class_day, time_index], major_index]:
                #      class_faculty.append(faculty)
                for major_faculty in faculty_by_major:
                    for faculty in major_faculty:
                        if faculty.class_times[0] == [[class_day, time_index], major_index] or faculty.class_times[1] == [[class_day, time_index], major_index]:
                            class_faculty.append(faculty)

                for building in time:
                    if len(class_faculty) < len(building.classrooms):
                        class_num = len(class_faculty)
                    else:
                        class_num = len(building.classrooms)

                    for i in range(class_num):
                        classroom = building.assign_agent(class_faculty[0])
                        class_faculty[0].classes.append(classroom)
                        class_faculty.remove(class_faculty[0])

    # if order of class times and classroom may not match, switch the order of first and second classroom to make it match
    for major_faculty in faculty_by_major:
        for faculty in major_faculty:
            if [faculty.classes[0].space.day, faculty.classes[0].space.time] != faculty.class_times[0][0]:
                second_class = faculty.classes[0]
                faculty.classes.remove(second_class)
                faculty.classes.append(second_class)  # remove and then append again to organize order

"""
for faculty in faculty_list:
    if len(faculty.classes) != 2:
        print("not assigned two classes")
    elif faculty.class_times[0][0] == faculty.class_times[1][0]:
        print("time conflict")
    else:
        print(faculty.classes)



for major in academic_buildings:
    for day in major:
        for time in day:
            for building in time:
                for classroom in building.classrooms:
                    print(classroom.faculty)
"""



# -----------------------------------------------------------------------------------------------------------------------------------
def assign_student_classes(day_time, academic_buildings, student_by_major):
    # assign two major classes to student agents
    for major_student in student_by_major:
        for agent in major_student:
            # for agent in student_list:
            day_time_copy = copy.copy(day_time)
            class_times = random.sample(day_time_copy, k=2)
            day_time_copy.remove(class_times[0])
            day_time_copy.remove(class_times[1])
            class_num = 0

            while class_num < 2:
                class_time = class_times[class_num]
                other_majors = [0, 1, 2]
                major_index = agent.get_major_index()
                other_majors.remove(major_index)

                if class_time[0] == "A":
                    day_index = 0
                else:  # if class_time[0] == "B"
                    day_index = 1
                time_index = class_time[1] // 2 - 1

                major_buildings = academic_buildings[major_index][day_index][
                    time_index]  # list of buildings at the corresponding [day, time]
                random.shuffle(major_buildings)

                while all(building.status == "Full" for building in major_buildings):
                    major_index = random.choice(other_majors)
                    major_buildings = academic_buildings[major_index][day_index][time_index]
                    other_majors.remove(major_index)

                for building in major_buildings:
                    if building.status == "Full":
                        continue
                    else:
                        classroom = building.assign_agent(agent)
                        agent.classes.append(classroom)
                        agent.class_times.append([class_time, major_index])
                        break

                class_num += 1

    # assign two other classes (not necessarily of their major) to student agents
    for major_student in student_by_major:
        for agent in major_student:
            # for agent in student_list:
            day_time_copy = copy.copy(day_time)
            day_time_copy.remove(agent.class_times[0][0])
            day_time_copy.remove(agent.class_times[1][0])
            class_times = random.sample(day_time_copy, k=2)
            day_time_copy.remove(class_times[0])
            day_time_copy.remove(class_times[1])
            class_num = 0

            while class_num < 2:
                class_time = class_times[class_num]
                other_majors = [0, 1, 2]
                major_index = random.randint(0, 2)
                other_majors.remove(major_index)

                if class_time[0] == "A":
                    day_index = 0
                else:  # if class_time[0] == "B"
                    day_index = 1
                time_index = class_time[1] // 2 - 1

                major_buildings = academic_buildings[major_index][day_index][
                    time_index]  # list of buildings at the corresponding [day, time]
                random.shuffle(major_buildings)

                while all(building.status == "Full" for building in major_buildings):
                    major_index = random.choice(other_majors)
                    major_buildings = academic_buildings[major_index][day_index][time_index]
                    other_majors.remove(major_index)

                for building in major_buildings:
                    if building.status == "Full":
                        continue
                    else:
                        classroom = building.assign_agent(agent)
                        agent.classes.append(classroom)
                        agent.class_times.append([class_time, major_index])
                        break

                class_num += 1


def add_class_to_schedule(agent_list):
    # after all agents have been assigned to classes, add the classes into their schedule attribute
    for agent in agent_list:
        # add assigned classes to agent's schedule attribute
        for classroom in agent.classes:
            i = agent.classes.index(classroom)
            class_time = agent.class_times[i][0]  # [day, time] of i-th class
            agent.schedule[class_time[0]][class_time[1]] = classroom
            agent.schedule[class_time[0]][class_time[1]+1] = classroom


# DINING HALL / GYM / LIBRARY ####################################################################################################################
# diningHallSpaces = createSpaces("DiningHall", 13) # We have unused Dining Hall spaces (at time 16) because the hours are not consecutive

def assign_dining_times(agent_list, diningHallSpaces):
    for agent in agent_list:  # Assign dining hall times to all agents
        if agent.type == "Off-campus Student":
            for day in SCHEDULE_WEEKDAYS:
                assign_meal(agent, day, 12, 15, diningHallSpaces)
        elif agent.type == "Faculty":
            for day in SCHEDULE_WEEKDAYS:
                assign_meal(agent, day, 11, 13, diningHallSpaces)
        else:
            for day in SCHEDULE_DAYS:
                assign_meal(agent, day, 8, 11, diningHallSpaces)
                assign_meal(agent, day, 12, 15, diningHallSpaces)
                assign_meal(agent, day, 17, 20, diningHallSpaces)



# gymSpaces = createSpaces("Gym")

def assign_gym(agent_list, gymSpaces):
    # Try to assign Gym slots
    for agent in agent_list:
        if agent.type != "Faculty":
            for count, day in enumerate(SCHEDULE_DAYS):
                if day == 'W' and agent.type == "Off-campus Student":
                    break
                rand_prob = random.random()
                if rand_prob < PROBABILITY_G:
                    available_times = agent.get_available_hours(8, 22, day)
                    gymHour = random.choice(available_times)
                    gymSpaces[count][gymHour].assign_agent(agent)


# Remaining slots for social spaces, library leaf, or dorm room
def assign_remaining_time(agent_list, library_spaces, social_spaces, stem_office_spaces, arts_office_spaces, humanities_office_spaces, off_campus_space):
    for agent in agent_list:
        if agent.type != "Faculty":
            for count, day in enumerate(SCHEDULE_DAYS):
                for hour in agent.get_available_hours(8, 22, day):
                    if day == 'W' and agent.type == "Off-campus Student":
                        off_campus_space[count][hour].assign_agent(agent)
                        continue
                    rand_number = random.random()
                    if rand_number < PROBABILITY_S:  # Assign social space
                        social_spaces[count][hour].assign_agent(agent)
                    elif rand_number < PROBABILITY_S + PROBABILITY_L:  # Assign library space
                        library_spaces[count][hour].assign_agent(agent)
                    else:  # Assign dorm room if on-campus, otherwise assign off-campus
                        if agent.type == "On-campus Student":
                            agent.schedule.get(day)[hour] = "Dorm"
                            if agent in doubles_students:
                                if agent.dorm_room in temp_doubles_dorm_times[count][hour]:
                                    doubles_dorm_times[count][hour].append(agent.dorm_room)
                                else:
                                    temp_doubles_dorm_times[count][hour].append(agent.dorm_room)
                        else:
                            off_campus_space[count][hour].assign_agent(agent)
        else:
            for count, day in enumerate(SCHEDULE_DAYS):
                for hour in agent.get_available_hours(8, 22, day):
                    if day == 'W':
                        off_campus_space[count][hour].assign_agent(agent)
                        continue
                    if hour == 0 or hour == 1 or hour >= 10 and hour <= 14:
                        off_campus_space[count][hour].assign_agent(agent)
                    else:  # Put into appropriate Division Office vertex
                        if agent.major == "STEM":
                            stem_office_spaces[count][hour].assign_agent(agent)
                        elif agent.major == "Arts":
                            arts_office_spaces[count][hour].assign_agent(agent)
                        else:  # Agent's major is Humanities
                            humanities_office_spaces[count][hour].assign_agent(agent)


