document.addEventListener('DOMContentLoaded', function() {
    // Load foods when page loads
    loadFoods();

    // Handle Add Food Form Submission
    const addFoodForm = document.getElementById('addFoodForm');
    if (addFoodForm) {
        addFoodForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(addFoodForm);
            
            fetch('/add_food', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showAlert('Food added successfully!', 'success');
                    addFoodForm.reset();
                    
                    // If we're on the add_food page, show a success message
                    if (window.location.pathname === '/add_food') {
                        const alertDiv = document.createElement('div');
                        alertDiv.className = 'alert alert-success mt-3';
                        alertDiv.textContent = 'Food added successfully!';
                        addFoodForm.parentNode.insertBefore(alertDiv, addFoodForm.nextSibling);
                        
                        // Remove the alert after 3 seconds
                        setTimeout(() => {
                            alertDiv.remove();
                        }, 3000);
                    }
                } else {
                    showAlert(data.message || 'Error adding food', 'danger');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showAlert('Error adding food', 'danger');
            });
        });
    }

    // Handle Food Detection Form Submission
    document.getElementById('detectFoodForm').addEventListener('submit', function(e) {
        e.preventDefault();
        
        const formData = new FormData(this);
        const submitButton = this.querySelector('button[type="submit"]');
        const resultDiv = document.getElementById('detectionResult');
        const resultContent = document.getElementById('resultContent');
        
        // Show loading state
        submitButton.disabled = true;
        submitButton.classList.add('btn-loading');
        submitButton.innerHTML = 'Detecting...';
        
        // Clear previous results
        resultContent.innerHTML = '<div class="text-center"><div class="spinner-border text-primary" role="status"></div><p class="mt-2">Analyzing image...</p></div>';
        resultDiv.style.display = 'block';
        
        // Create a preview of the uploaded image
        const imageFile = formData.get('image');
        if (imageFile) {
            const reader = new FileReader();
            reader.onload = function(e) {
                const imgPreview = document.createElement('img');
                imgPreview.src = e.target.result;
                imgPreview.classList.add('result-image', 'img-fluid', 'rounded', 'mb-3');
                resultContent.insertBefore(imgPreview, resultContent.firstChild);
            };
            reader.readAsDataURL(imageFile);
        }
        
        // Send the image to the server for detection
        fetch('/detect_food', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Create the result HTML
            let resultHTML = `
                <div class="alert alert-info">
                    <h5 class="mb-2">Detected Food: ${data.name}</h5>
                    <span class="confidence-badge ${getConfidenceClass(data.confidence_level)}">
                        Confidence: ${data.confidence}%
                    </span>
                </div>
                
                <div class="nutrition-summary">
                    <h6>Nutritional Information</h6>
                    <div class="row">
                        <div class="col-md-6">
                            <p><strong>Proteins:</strong> ${data.proteins}g</p>
                            <p><strong>Fats:</strong> ${data.fats}g</p>
                            <p><strong>Carbohydrates:</strong> ${data.carbohydrates}g</p>
                        </div>
                        <div class="col-md-6">
                            <p><strong>Fibers:</strong> ${data.fibers}g</p>
                            <p><strong>Calories:</strong> ${data.calories}</p>
                        </div>
                    </div>
                </div>
            `;
            
            // Add feature comparison if available
            if (data.feature_comparison && data.feature_comparison.length > 0) {
                const comparison = data.feature_comparison;
                resultHTML += `
                    <div class="feature-comparison">
                        <h6>Detection Analysis</h6>
                        <p>The system compared your image with multiple food items in the database:</p>
                        <ul>
                            <li><strong>Best Match:</strong> ${comparison.top_match} (${comparison.confidence}% confidence)</li>
                            <li><strong>Second Best:</strong> ${comparison.second_match}</li>
                            <li><strong>Score Difference:</strong> ${comparison.score_difference}%</li>
                        </ul>
                        <p>${getConfidenceExplanation(comparison.confidence, comparison.score_difference)}</p>
                    </div>
                `;
            }
            
            // Add pre-trained model predictions if available
            if (data.model_predictions && data.model_predictions.length > 0) {
                resultHTML += `
                    <div class="model-predictions">
                        <h6>AI Model Predictions</h6>
                        <p>The pre-trained AI model identified the following food items:</p>
                        <table class="table table-sm">
                            <thead>
                                <tr>
                                    <th>Food Item</th>
                                    <th>Confidence</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${data.model_predictions.map(pred => `
                                    <tr>
                                        <td>${pred.name}</td>
                                        <td>
                                            <div class="progress" style="height: 20px;">
                                                <div class="progress-bar ${getConfidenceClass(getConfidenceLevel(pred.probability))}" 
                                                     role="progressbar" 
                                                     style="width: ${pred.probability}%;" 
                                                     aria-valuenow="${pred.probability}" 
                                                     aria-valuemin="0" 
                                                     aria-valuemax="100">
                                                    ${pred.probability.toFixed(2)}%
                                                </div>
                                            </div>
                                        </td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                `;
            }
            
            // Add top matches if available
            if (data.top_matches && data.top_matches.length > 1) {
                resultHTML += `
                    <div class="top-matches">
                        <h6>Other Possible Matches</h6>
                        <table class="table table-sm">
                            <thead>
                                <tr>
                                    <th>Food</th>
                                    <th>Match Score</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${data.top_matches.slice(1).map(match => `
                                    <tr>
                                        <td>${match.name}</td>
                                        <td>
                                            <div class="progress" style="height: 20px;">
                                                <div class="progress-bar ${getConfidenceClass(getConfidenceLevel(match.score))}" 
                                                     role="progressbar" 
                                                     style="width: ${match.score}%;" 
                                                     aria-valuenow="${match.score}" 
                                                     aria-valuemin="0" 
                                                     aria-valuemax="100">
                                                    ${match.score}%
                                                </div>
                                            </div>
                                        </td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                `;
            }
            
            // Add feature comparison explanation
            resultHTML += `
                <div class="feature-comparison">
                    <h6>How It Works</h6>
                    <p>The system uses a pre-trained deep learning model (ResNet50) to analyze your image:</p>
                    <ul>
                        <li><strong>Deep Learning:</strong> The model has been trained on millions of images to recognize thousands of food items</li>
                        <li><strong>Feature Extraction:</strong> The model extracts high-level features from the image</li>
                        <li><strong>Database Matching:</strong> The system compares these features with your food database</li>
                        <li><strong>Confidence Scoring:</strong> A confidence score is calculated based on the similarity</li>
                    </ul>
                    <p>The confidence score represents how closely your image matches the identified food item.</p>
                </div>
            `;
            
            // Update the result content
            resultContent.innerHTML = resultHTML;
        })
        .catch(error => {
            resultContent.innerHTML = `
                <div class="alert alert-danger">
                    <h5>Error</h5>
                    <p>${error.message || 'An error occurred during food detection.'}</p>
                </div>
            `;
        })
        .finally(() => {
            // Reset button state
            submitButton.disabled = false;
            submitButton.classList.remove('btn-loading');
            submitButton.innerHTML = 'Detect Food';
        });
    });

    // Train Model Button Click Handler
    const trainModelBtn = document.getElementById('trainModelBtn');
    const trainingStatus = document.getElementById('trainingStatus');
    const trainingProgress = document.getElementById('trainingProgress');
    const trainingMessage = document.getElementById('trainingMessage');
    const lastTrainingDate = document.getElementById('lastTrainingDate');
    
    if (trainModelBtn) {
        // Load model status on page load
        fetch('/model_status')
            .then(response => response.json())
            .then(data => {
                if (data.success && lastTrainingDate) {
                    lastTrainingDate.textContent = data.last_training;
                }
            })
            .catch(error => {
                console.error('Error loading model status:', error);
            });
        
        trainModelBtn.addEventListener('click', function() {
            // Show training status
            if (trainingStatus) trainingStatus.style.display = 'block';
            trainModelBtn.disabled = true;
            trainModelBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Training...';
            
            // Start with a small progress to show activity
            if (trainingProgress) {
                trainingProgress.style.width = '10%';
                trainingProgress.setAttribute('aria-valuenow', 10);
                trainingProgress.textContent = '10%';
            }
            if (trainingMessage) trainingMessage.textContent = 'Initializing training...';
            
            // Call the train_model endpoint
            fetch('/train_model', {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update progress to 100%
                    if (trainingProgress) {
                        trainingProgress.style.width = '100%';
                        trainingProgress.setAttribute('aria-valuenow', 100);
                        trainingProgress.textContent = '100%';
                    }
                    if (trainingMessage) trainingMessage.textContent = 'Training completed successfully!';
                    
                    // Update last training date
                    if (lastTrainingDate) {
                        lastTrainingDate.textContent = data.training_date;
                    }
                    
                    // Show success message
                    const alertDiv = document.createElement('div');
                    alertDiv.className = 'alert alert-success mt-3';
                    alertDiv.textContent = `Model trained successfully! Trained on ${data.foods_trained} food items.`;
                    trainingStatus.parentNode.insertBefore(alertDiv, trainingStatus.nextSibling);
                    
                    // Remove the alert after 5 seconds
                    setTimeout(() => {
                        alertDiv.remove();
                    }, 5000);
                } else {
                    // Show error message
                    if (trainingMessage) trainingMessage.textContent = `Error: ${data.message}`;
                    
                    const alertDiv = document.createElement('div');
                    alertDiv.className = 'alert alert-danger mt-3';
                    alertDiv.textContent = `Training failed: ${data.message}`;
                    trainingStatus.parentNode.insertBefore(alertDiv, trainingStatus.nextSibling);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                if (trainingMessage) trainingMessage.textContent = 'Error during training';
                
                const alertDiv = document.createElement('div');
                alertDiv.className = 'alert alert-danger mt-3';
                alertDiv.textContent = 'Error during training. Please try again.';
                trainingStatus.parentNode.insertBefore(alertDiv, trainingStatus.nextSibling);
            })
            .finally(() => {
                // Re-enable the button
                trainModelBtn.disabled = false;
                trainModelBtn.innerHTML = 'Train Model';
            });
        });
    }
});

// Function to load and display foods
function loadFoods() {
    fetch('/foods')
        .then(response => response.json())
        .then(foods => {
            const foodList = document.getElementById('foodList');
            foodList.innerHTML = '';
            
            foods.forEach(food => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>
                        <img src="${food.image_path || '/static/placeholder.jpg'}" 
                             alt="${food.name}" 
                             class="food-image"
                             onerror="this.onerror=null; this.src='/static/placeholder.jpg';"
                             loading="lazy">
                    </td>
                    <td>${food.name}</td>
                    <td>${food.proteins}g</td>
                    <td>${food.fats}g</td>
                    <td>${food.carbs}g</td>
                    <td>${food.fiber}g</td>
                    <td>${food.calories} kcal</td>
                `;
                foodList.appendChild(row);
            });
        })
        .catch(error => {
            console.error('Error loading foods:', error);
            showAlert('Error loading food database', 'danger');
        });
}

// Function to show alerts
function showAlert(type, message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    const container = document.querySelector('.container');
    container.insertBefore(alertDiv, container.firstChild);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

// Helper function to get confidence class based on level
function getConfidenceClass(level) {
    switch(level) {
        case 'high':
            return 'confidence-high';
        case 'medium':
            return 'confidence-medium';
        case 'low':
        default:
            return 'confidence-low';
    }
}

// Helper function to determine confidence level from score
function getConfidenceLevel(score) {
    if (score > 70) return 'high';
    if (score > 50) return 'medium';
    return 'low';
}

// Helper function to get confidence explanation
function getConfidenceExplanation(confidence, scoreDiff) {
    if (confidence > 80) {
        return "The system is highly confident in this identification.";
    } else if (confidence > 60) {
        if (scoreDiff > 20) {
            return "The system is moderately confident in this identification, with a significant difference from other potential matches.";
        } else {
            return "The system is moderately confident in this identification, but there are other similar matches in the database.";
        }
    } else {
        if (scoreDiff > 10) {
            return "The system has low confidence in this identification, but it is still the best match among the available options.";
        } else {
            return "The system has low confidence in this identification. The image may not match any food in the database well.";
        }
    }
} 