## Football Tracking and Analysis System

## Background
Football is a very popular sport around the world, with millions of fans and players from various backgrounds. Along with the development of technological analysis, football matches have undergone significant transformation, especially with the adoption of Artificial Intelligence (AI) and computer vision technology. Analysis of tracking the movement and position of the ball in a match analysis can be the material needed by a team in a team. The use of technology in this case allows for a more in-depth and objective analysis of the game, which is more complex using technology.

## Objective
- Tracking the presence of players, referees and the ball on the screen
- Tracking the speed of player movement
- Tracking possession of the ball by each team
- Tracking the distance traveled by each player

## Dataset
This dataset is used to train a YOLO model to detect players, referees, goalkeepers, and the ball within the field area.

Link : https://universe.roboflow.com/roboflow-jvuqo/football-players-detection-3zvbc/dataset/1/images

## Dataset for testing
This dataset is used to test the system.

Link : https://www.kaggle.com/datasets/saberghaderi/-dfl-bundesliga-460-mp4-videos-in-30sec-csv

## Implementation Process
- Dataset Preparation
- Model design and training
- Post detection processing
- Detection Testing
- System development and integration

## Feature
- Player Detection with each team color
- Ball tracker
- Player speed detector and distance covered
- Ball possession for each team

## Model Accuracy
![image](https://github.com/user-attachments/assets/9743f572-9192-49cf-9fe7-58401c26525a)
Using the YOLOv5x model trained with the roboflow dataset to add 4 labels and detect objects in the field.

## Result
UI: 
![image](https://github.com/user-attachments/assets/fc692663-fc35-44d8-bfa9-e805fa8bcda1)


Result: 
![video](https://github.com/user-attachments/assets/3daf8ebe-dfd8-4a7f-aa6f-fd7eaca96efc)


Result (Challenge)
![video](https://github.com/user-attachments/assets/4923afd6-b035-410f-a19f-bd7c3627f31a)


