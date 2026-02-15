from flask import Flask, render_template, request
import numpy as np
from sklearn.neighbors import NearestNeighbors

app = Flask(__name__)

workouts = {
    "fat_loss": {
        "beginner": [
            ("Marching in Place", "5 min", "Warm-up, Low impact"),
            ("Brisk Walking", "10 min", "Cardio"),
            ("Bodyweight Squats", "3 x 12", "Legs"),
            ("Standing Crunches", "3 x 15", "Core"),
            ("Stretching", "5 min", "Cool-down")
        ],
        "intermediate": [
            ("Jumping Jacks", "5 min", "Warm-up, Cardio"),
            ("Lunges", "3 x 12", "Legs"),
            ("Push-ups", "3 x 12", "Chest"),
            ("Plank", "3 x 30 sec", "Core"),
            ("Stretching", "5 min", "Cool-down")
        ],
        "advanced": [
            ("Burpees", "5 min", "Warm-up, Cardio"),
            ("Squat Jumps", "3 x 15", "Legs"),
            ("Push-ups", "4 x 15", "Chest"),
            ("Mountain Climbers", "3 x 30 sec", "Core"),
            ("Stretching", "5 min", "Cool-down")
        ]
    },
    "muscle_gain": {
        "beginner": [
            ("Marching in Place", "5 min", "Warm-up, Low impact"),
            ("Bodyweight Squats", "3 x 12", "Legs"),
            ("Push-ups", "3 x 12", "Chest"),
            ("Standing Crunches", "3 x 15", "Core"),
            ("Stretching", "5 min", "Cool-down")
        ],
        "intermediate": [
            ("Jumping Jacks", "5 min", "Warm-up, Cardio"),
            ("Dumbbell Squats", "3 x 12", "Legs"),
            ("Push-ups", "4 x 12", "Chest"),
            ("Plank", "3 x 45 sec", "Core"),
            ("Stretching", "5 min", "Cool-down")
        ],
        "advanced": [
            ("Burpees", "5 min", "Warm-up, Cardio"),
            ("Deadlifts", "4 x 12", "Legs"),
            ("Bench Press", "4 x 12", "Chest"),
            ("Plank", "4 x 1 min", "Core"),
            ("Stretching", "5 min", "Cool-down")
        ]
    }
}

meals = [
    {"name": "Oats with Milk", "calories": 250, "protein": 10, "carbs": 40, "fat": 5, "type": "veg"},
    {"name": "Egg White Omelette", "calories": 200, "protein": 18, "carbs": 2, "fat": 10, "type": "non-veg"},
    {"name": "Grilled Paneer Salad", "calories": 300, "protein": 15, "carbs": 10, "fat": 20, "type": "veg"},
    {"name": "Chicken Salad", "calories": 350, "protein": 30, "carbs": 5, "fat": 15, "type": "non-veg"},
    {"name": "Brown Rice & Veg Curry", "calories": 400, "protein": 10, "carbs": 60, "fat": 10, "type": "veg"},
    {"name": "Grilled Fish with Veggies", "calories": 400, "protein": 35, "carbs": 5, "fat": 15, "type": "non-veg"}
]

def filter_workout_by_time(workout_plan, time):
    if time == "15 mins":
        return workout_plan[:2]
    elif time == "30 mins":
        return workout_plan[:3]
    elif time == "45 mins":
        return workout_plan[:4]
    else:
        return workout_plan

def ai_select_exercises(exercises, user_goal, bmi_status, level):
    scored_exercises = []
    for exercise in exercises:
        name, duration, focus = exercise
        score = 0

        if user_goal == "fat_loss" and ("Cardio" in focus or "HIIT" in focus):
            score += 2
        if user_goal == "muscle_gain" and ("Chest" in focus or "Legs" in focus):
            score += 2

        if bmi_status in ["Overweight", "Obese"] and "Low impact" in focus:
            score += 1
        if bmi_status == "Underweight" and "Bodyweight" in focus:
            score += 1

        if level == "beginner" and "Advanced" not in name:
            score += 1
        if level == "advanced" and "Advanced" in name:
            score += 2

        scored_exercises.append((exercise, score))

    scored_exercises.sort(key=lambda x: x[1], reverse=True)
    top_exercises = [e[0] for e in scored_exercises[:5]]
    return top_exercises

def ml_select_meals(user_goal, bmi_status, diet_pref):
    goal_num = 1 if user_goal == "muscle_gain" else 0
    bmi_num = {"Underweight":0, "Normal":1, "Overweight":2, "Obese":3}[bmi_status]

    X = []
    meal_names = []
    for meal in meals:
        if meal["type"] == diet_pref or diet_pref=="both":
            X.append([meal["calories"], meal["protein"], meal["carbs"], meal["fat"]])
            meal_names.append(meal["name"])
    X = np.array(X)
    query = np.array([[2000 + goal_num*200, 50 + goal_num*20, 200, 50 + bmi_num*10]])
    
    knn = NearestNeighbors(n_neighbors=3)
    knn.fit(X)
    distances, indices = knn.kneighbors(query)
    selected_meals = [meal_names[i] for i in indices[0]]
    return selected_meals

def calculate_bmi(weight, height):
    bmi = weight / ((height/100)**2)
    if bmi < 18.5:
        return round(bmi,1), "Underweight"
    elif bmi < 25:
        return round(bmi,1), "Normal"
    elif bmi < 30:
        return round(bmi,1), "Overweight"
    else:
        return round(bmi,1), "Obese"

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        age = int(request.form.get("age"))
        weight = float(request.form.get("weight"))
        height = float(request.form.get("height"))
        goal = request.form.get("goal")             # "fat_loss" or "muscle_gain"
        level = request.form.get("level")           # beginner, intermediate, advanced
        diet_pref = request.form.get("diet")        # veg, non-veg, both
        time = request.form.get("time")             # 15, 30, 45, 60 mins

        # BMI calculation
        bmi_value, bmi_status = calculate_bmi(weight, height)

        full_plan = workouts[goal][level]
        ai_plan = ai_select_exercises(full_plan, goal, bmi_status, level)
        workout_plan = filter_workout_by_time(ai_plan, time)

        diet_result = ml_select_meals(goal, bmi_status, diet_pref)
        breakfast = diet_result[0]
        lunch = diet_result[1]
        dinner = diet_result[2]

        return render_template("index.html",
                               workout_plan=workout_plan,
                               breakfast=breakfast,
                               lunch=lunch,
                               dinner=dinner,
                               bmi_value=bmi_value,
                               bmi_status=bmi_status)
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
