const modelSelection = document.getElementById('model-selection');
const linearRegressionFeatures = document.getElementById('linear-regression-features');
const randomForestFeatures = document.getElementById('random-forest-features');

function showLinearRegressionFeatures() {
    linearRegressionFeatures.style.display = 'block';
    randomForestFeatures.style.display = 'none';
}

function showRandomForestFeatures() {
    linearRegressionFeatures.style.display = 'none';
    randomForestFeatures.style.display = 'block';
}

function setRequiredAttributes(container, isRequired) {
    const inputs = container.getElementsByTagName('input');
    for (let input of inputs) {
        input.required = isRequired;
    }
}

document.getElementById('prediction-form').addEventListener('submit', async function(event) {
    event.preventDefault();
    
    // Loader to await the API response
    document.getElementById('loader').style.display = 'block';

    const selectedModel = modelSelection.value;
    const feature1 = parseInt(document.getElementById('feature1').value);
    const feature2 = parseInt(document.getElementById('feature2').value);

    let apiUrl;
    let input_features;

    if (selectedModel === 'random_forest') {
        apiUrl = 'https://recipes-model-v1-kon5xeyahq-ue.a.run.app/predict_random_forest';
        const feature3 = parseInt(document.getElementById('feature4').value);
        const feature4 = parseInt(document.getElementById('feature4').value);
        const feature5 = parseInt(document.getElementById('feature5').value);
        const feature6 = parseInt(document.getElementById('feature6').value);
        const feature7 = parseInt(document.getElementById('feature7').value);
        const feature8 = parseInt(document.getElementById('feature8').value);
        input_features = [feature1, feature2, feature3, feature4, feature5, feature6, feature7, feature8];
    } else {
        apiUrl = 'https://recipes-model-v1-kon5xeyahq-ue.a.run.app/predict_linear_regression';
        const feature4 = parseInt(document.getElementById('feature4').value);
        const feature5 = parseInt(document.getElementById('feature5').value);
        const feature6 = parseInt(document.getElementById('feature6').value);
        const feature7 = parseInt(document.getElementById('feature7').value);
        const feature8 = parseInt(document.getElementById('feature8').value);
        const feature13 = parseInt(document.getElementById('feature13').value);
        input_features = [feature1, feature2, feature4, feature5, feature6, feature7, feature8, feature13];
    }

    const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ input_features: input_features })
    });

    // Hide loader
    document.getElementById('loader').style.display = 'none';

    if (response.ok) {
        const prediction = await response.json();
        const unit = selectedModel === 'random_forest' ? ' kcal' : ' minutes';
        document.getElementById('result').innerHTML = 'Prediction: ' + prediction + unit;
    } else {
    document.getElementById('result').innerHTML = 'Error: ' + response.statusText;
}
});

// Back Button
const backButton = document.getElementById('back-button');

backButton.addEventListener('click', () => {
    predictionForm.style.display = 'none';
    modelSelectionDiv.style.display = 'flex';
    result.innerHTML = '';
});

// Model selection event listeners
const linearRegressionOption = document.getElementById('linear-regression-option');
const randomForestOption = document.getElementById('random-forest-option');
const modelSelectionDiv = document.getElementById('model-selection');
const predictionForm = document.getElementById('prediction-form');

linearRegressionOption.addEventListener('click', () => {
    document.querySelector('h1').innerText = 'Linear Regression Model (Cook Time)';
    modelSelectionDiv.style.display = 'none';
    predictionForm.style.display = 'block';
    showLinearRegressionFeatures();

    // Set required attributes
    setRequiredAttributes(linearRegressionFeatures, true);
    setRequiredAttributes(randomForestFeatures, false);
});

randomForestOption.addEventListener('click', () => {
    document.querySelector('h1').innerText = 'Random Forest Model (Calories)';
    modelSelectionDiv.style.display = 'none';
    predictionForm.style.display = 'block';
    showRandomForestFeatures();

    // Set required attributes
    setRequiredAttributes(linearRegressionFeatures, false);
    setRequiredAttributes(randomForestFeatures, true);
});

// Change required fields based on the model selected
linearRegressionOption.addEventListener('click', () => {
    modelSelectionDiv.style.display = 'none';
    predictionForm.style.display = 'block';
    showLinearRegressionFeatures();

    // Set required attributes
    setRequiredAttributes(linearRegressionFeatures, true);
    setRequiredAttributes(randomForestFeatures, false);
});

randomForestOption.addEventListener('click', () => {
    modelSelectionDiv.style.display = 'none';
    predictionForm.style.display = 'block';
    showRandomForestFeatures();

    // Set required attributes
    setRequiredAttributes(linearRegressionFeatures, false);
    setRequiredAttributes(randomForestFeatures, true);
});