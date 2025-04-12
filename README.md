# Food Nutrition Tracker

A web application that allows users to track food nutrition information and detect food items from images.

## Features

- Add new food items with nutritional information
- Upload food images
- Detect food items from images
- View a database of all added foods
- Modern and responsive UI

## Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd food-nutrition-tracker
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

4. Create the necessary directories:
```bash
mkdir static/uploads
```

## Running the Application

1. Start the Flask server:
```bash
python app.py
```

2. Open your web browser and navigate to:
```
http://localhost:5000
```

## Usage

1. Adding a New Food:
   - Fill in the food details (name, proteins, fats, etc.)
   - Optionally upload a food image
   - Click "Add Food" to save

2. Detecting Food from Image:
   - Upload a food image
   - Click "Detect Food" to get nutritional information
   - The system will display the detected food's details

3. Viewing Food Database:
   - All added foods are displayed in the table below
   - Images are shown if available
   - Nutritional information is displayed in a clear format

## Note

The food detection feature currently returns dummy data. To implement actual food detection, you would need to integrate with a food recognition API (such as Google Cloud Vision API or a similar service).

## License

This project is licensed under the MIT License - see the LICENSE file for details. 