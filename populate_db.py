from app import db, FoodItem, Nutrient, AlternativeFood
import csv
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

def populate_nutrients_and_alternatives(nutrient_file, alternative_file):
    with open(nutrient_file, 'r') as file:
        reader = csv.reader(file)
        next(reader)
        for row in reader:
            food_name = row[1]
            nutrient_name = row[2]
            amount_per_unit = float(row[3])
            food_item = FoodItem.query.filter_by(name=food_name).first()
            if food_item:
                nutrient = Nutrient(food_id=food_item.id, nutrient_name=nutrient_name, amount_per_unit=amount_per_unit)
                db.session.add(nutrient)
        db.session.commit()

    with open(alternative_file, 'r') as file:
        reader = csv.reader(file)
        next(reader)
        for row in reader:
            food_name = row[1]
            alternative_food_name = row[2]
            food_item = FoodItem.query.filter_by(name=food_name).first()
            if food_item:
                alternative = AlternativeFood(food_id=food_item.id, alternative_food_name=alternative_food_name)
                db.session.add(alternative)
        db.session.commit()

if __name__ == '__main__':
    from app import app
    with app.app_context():
        db.create_all()
        populate_food_items('calories_dataset_for_mp.csv')
        populate_nutrients_and_alternatives('nutrients_dataset.csv', 'alternatives_dataset.csv')
