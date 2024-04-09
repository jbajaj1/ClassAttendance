import os
import csv
import shutil
from dateutil import parser
import pandas as pd
import tempfile

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

folder_source = "./Untracked/"
destination_source = "./Tracked/"

roster = "./PSYC261-SP24_Class_Roster.csv"
tracked_attendance = "./PSYC261-Attendance-S24.csv"

excused_list = "./excused_attendance.csv"
tracked_excused_list = "./Tracked/excused_attendance_tracked.csv"

added_list = "./added_attendance.csv"
tracked_added_list = "./Tracked/added_attendance_tracked.csv"

def parse_date(date_string):
    date_object = None

    parsed_date = parser.parse(date_string, default=None)

    if parsed_date is not None:
        date_object = parsed_date.date()

    return str(date_object)

def read_csv_files(folder_source, destination_source, attendance):
    if not os.path.isdir(folder_source):
        print(f'{folder_source} is not a valid directory')
        return

    files = os.listdir(folder_source)

    csv_files = [file for file in files if file.endswith('.csv')]

    for csv_file in csv_files:
        folder_path = os.path.join(folder_source, csv_file)
        destination_path = os.path.join(destination_source, csv_file)

        with open(folder_path, 'r') as file:
            csv_reader = csv.reader(file)
            process_csv_file(csv_reader, attendance)


        shutil.move(folder_path, destination_path)
        print(f"Moved {csv_file} to {destination_source}\n")
    return attendance

def process_csv_file(csv_reader, attendance):
    #Skip header
    next(csv_reader)

    # Iterate over rows in the CSV file
    for row in csv_reader:
        row[0] = parse_date(row[0].split(" ")[0])
        row = row[:-1]
        row.append("A")
        if row[0] not in attendance:
            attendance[row[0]] = [row[1:]]
        else:
            attendance[row[0]].append(row[1:])

    return attendance


#Need to make a case for excused of different day
def process_excused(excused_list, tracked_excused_list, dates):
    excused_attendance = {}
    excused_csv = open(excused_list, 'r')
    csv_reader = csv.reader(excused_csv)

    tracked_csv = open(tracked_excused_list, 'a', newline='')
    tracked_writer = csv.writer(tracked_csv)

    out_of_bounds_dates = []

    for row in csv_reader:
        row[2] = parse_date(row[2])
        excused_person = row[:-1]
        excused_person.append("E")
        if row[2] in dates:
            if row[2] in excused_attendance:
                excused_attendance[row[2]].append(excused_person)
            else:
                excused_attendance[row[2]] = [excused_person]
            tracked_writer.writerow(row)
        else:
            out_of_bounds_dates.append(row)
    excused_csv.close()

    excused_csv = open(excused_list, 'w')
    excused_csv_writer = csv.writer(excused_csv)
    for row in out_of_bounds_dates:
        excused_csv_writer.writerow(row)

    return excused_attendance

def match_roster(attendance, roster, excused=False):
    roster_csv = open(roster, 'r')
    roster_reader = csv.reader(roster_csv)
    header = next(roster_reader)

    roster_names = []

    for name in roster_reader:
        roster_names.append((name[0], name[1]))

    records = {}

    for day in attendance:
        records[day] = []

        for name in attendance[day]:
            name[0] = name[0].strip().title()
            name[1] = name[1].strip().title()

            full_name = (name[0], name[1])
            matched, proper_name = name_match(full_name, roster_names)

            if not matched:
                print(full_name, "is a flagged name!!", day)
            else:
                name[0] = proper_name[0]
                name[1] = proper_name[1]
                if name not in records[day]:
                    records[day].append(name)

    for day in records:
        if not excused:
            for name in roster_names:
                no_match = True
                for n in records[day]:
                    if n[0] == name[0] and n[1] == name[1]:
                        no_match = False
                if no_match:
                    print(day, name[0], name[1], "Absence -- is it excused?")
                    records[day].append([name[0], name[1], "U"])
        records[day] = sorted(records[day], key=lambda x: (x[0], x[1]))
    
    return records

def update_attendance(records, tracked_attendance):
    if records == {}:
        return 0
    with open(tracked_attendance, 'r', newline='', encoding='utf-8') as infile:
        reader = csv.reader(infile)
        header = next(reader)  # Assuming the CSV file has a header row
        rows = list(reader)

    data_column = {}
    for day in sorted(records.keys()):
        # Append the new column name to the header
        header.append(day)
        data_column[day] = []
        for name in records[day]:
            data_column[day].append(name[-1])

    data_list = [list(items) for items in zip(*data_column.values())]
    data = [row + data_list[i] for i, row in enumerate(rows)]
    
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, newline='', encoding='utf-8')

    # Write the modified data to the temporary file
    with open(temp_file.name, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(header)
        writer.writerows(data)
    # Replace the original file with the temporary file
    shutil.move(temp_file.name, tracked_attendance)


def name_match(full_name, roster_names):
    last_name = full_name[0].split(" ")
    first_name = full_name[1].split(" ")
    for name in roster_names:
        for l in last_name:
            for f in first_name:
                if l in name[0] and f in name[1]:
                    return True, (name[0], name[1])
                if f in name[0] and l in name[1]:
                    return True, (name[0], name[1])
                if l in name[0] and f[0] == name[1][0] and "Jr" not in l:
                    return True, (name[0], name[1])
                if f in name[0] and l[0] == name[1][0] and "Jr" not in f:
                    return True, (name[0], name[1])
                if name[0] == "Flores Rivas" and name[1] == "Rosmery" and (f == "Rosmery" or f == "Flores") and (l == "Rivasflores" or l == "Rivas"):
                    return True, (name[0], name[1])
    return False, ("null", "null")

def update_attendance_excused(excused_records, tracked_attendance):
    attendance_df = pd.read_csv(tracked_attendance)
    for day in excused_records:
        for person in excused_records[day]:
            last_name = person[0]
            first_name = person[1]
            attendance_df.loc[(attendance_df['Last Name'] == last_name) & (attendance_df['First Name'] == first_name), day] = 'E'
    attendance_df.to_csv(tracked_attendance, index=False)
    

def extract_dates(tracked_attendance):
    with open(tracked_attendance, 'r', newline='') as file:
        csv_reader = csv.reader(file)
        headers = next(csv_reader)  # Read the first row which contains headers
    return headers[8:]

def calculate_attendance(tracked_attendance):
    calculated_attendance_rows = []
    with open(tracked_attendance, 'r', newline='') as file:
        csv_reader = csv.reader(file)
        headers = next(csv_reader)  # Read the first row which contains headers
        calculated_attendance_rows.append(headers)
        for student in csv_reader:
            attendance_record = student[12:]
            total_attended = 0
            total_excused = 0
            total_unexcused = 0
            for day in attendance_record:
                if day == 'A':
                    total_attended += 1
                if day == "E":
                    total_excused += 1
                if day == "U":
                    total_unexcused += 1
            total_attended_and_excused = total_attended + total_excused
            calc_record = student[0:4] + [total_attended, total_excused, total_attended_and_excused, total_unexcused] + student[8:]
            calculated_attendance_rows.append(calc_record)

    with open(tracked_attendance, 'w', newline='') as file:
        csv_writer = csv.writer(file)
        csv_writer.writerows(calculated_attendance_rows)


def report_unattended(tracked_attendance):
    attendance_df = pd.read_csv(tracked_attendance)
    # Filter the DataFrame to include only rows with more than 3 unexcused absences
    filtered_df = attendance_df[attendance_df['Total Unexcused (post 2/8)'] > 2]

    # Get the list of people who have more than 3 unexcused absences
    people_with_more_than_3_unexcused = filtered_df[['Last Name', 'First Name', 'Username', 'Total Unexcused (post 2/8)']].values.tolist()

    print("People with 3 or more unexcused absences:")
    for person in people_with_more_than_3_unexcused:
        print(f"{person[0]}, {person[1]}, {person[2]}, {person[3]}")

def process_added(added_list, tracked_added_list, dates):
    added_records = {}

    added_csv = open(added_list, 'r')
    csv_reader = csv.reader(added_csv)

    tracked_csv = open(tracked_added_list, 'a', newline='')
    tracked_writer = csv.writer(tracked_csv)

    for row in csv_reader:
        row[2] = parse_date(row[2])
        added_person = row[:-1]
        if row[2] in dates:
            if row[2] in added_records:
                added_records[row[2]].append(added_person)
            else:
                added_records[row[2]] = [added_person]
        tracked_writer.writerow(row)
    added_csv.close()
    added_csv = open(added_list, 'w')

    return added_records

def update_attendance_added(added_records, tracked_attendance):

    attendance_df = pd.read_csv(tracked_attendance)
    for day in added_records:
        for person in added_records[day]:
            last_name = person[0]
            first_name = person[1]
            attendance_df.loc[(attendance_df['Last Name'] == last_name) & (attendance_df['First Name'] == first_name), day] = 'A'
    attendance_df.to_csv(tracked_attendance, index=False)


attendance = {}
attendance = read_csv_files(folder_source, destination_source, attendance)

records = match_roster(attendance, roster)
update_attendance(records, tracked_attendance)

dates = extract_dates(tracked_attendance)
excused_attendance = process_excused(excused_list, tracked_excused_list, dates)

excused_records = match_roster(excused_attendance, roster, excused=True)
update_attendance_excused(excused_records, tracked_attendance)

added_records = process_added(added_list, tracked_added_list, dates)
update_attendance_added(added_records, tracked_attendance)

calculate_attendance(tracked_attendance)

report_unattended(tracked_attendance)
