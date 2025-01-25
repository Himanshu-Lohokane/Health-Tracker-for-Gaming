# Health-Tracker-for-Gaming
In addition to tracking the game that is currently playing and offering helpful advice like water consumption and break recommendations, this project assists users in tracking their posture data. Additionally, machine learning algorithms and visualizations are used to improve the meaningfulness of the data.

main.py
This file is the one that that opens up the program that tracks the time and the posture data and creates a log file of the collected data. This data is saved in the .db file automatically but if u want to use this data for visualization then press the export logs button to save it to a csv file.

visualization.py
This is the file that will open up the charts on the collected data and will also show all the ML generated data charts one by one.

data_inserter_for_testing.py
insert data into the db and csv file for testing the graphs(if u do not have enough data at the start)

## additional info
delete the .db and .csv file for creating a completely new database for yourself.
