import csv
from app import db, FoodItem

def populate_food_items(csv_file):
    with open(csv_file, 'r') as file:
        reader = csv.reader(file)
        next(reader)
        for row in reader:
            food_name = row[1]
            calories_per_100g = float(row[3].split()[0]) 
            food_item = FoodItem(name=food_name, calories_per_unit=calories_per_100g)
            db.session.add(food_item)
        db.session.commit()

if __name__ == '__main__':
    from app import app
    with app.app_context():
        db.create_all()
        populate_food_items('calories dataset for mp.csv')
