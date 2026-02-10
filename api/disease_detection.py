import os
import numpy as np
from PIL import Image
from io import BytesIO
import base64
import json
import time


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET


# Import TensorFlow Lite
try:
    import tensorflow as tf
    Interpreter = tf.lite.Interpreter
    USE_TF = True
except ImportError:
    try:
        import tflite_runtime.interpreter as tflite  # type: ignore
        Interpreter = tflite.Interpreter  # type: ignore
        USE_TF = False
    except ImportError:
        Interpreter = None  # type: ignore
        USE_TF = None


from .models import DiseaseDetectionLog


# Confidence threshold - minimum confidence to accept a prediction
CONFIDENCE_THRESHOLD = 70.0  # Increased threshold to reduce false positives

# Minimum green pixel percentage for leaf detection
MIN_GREEN_PERCENTAGE = 5.0  # Image should have at least 5% green pixels

# Disease labels - must match your model's output order
DISEASE_LABELS = [
    'Birds-eye',
    'Colletorichum-leaf-disease',
    'Corynespora',
    'Healthy',
    'Pesta',
    'Powdery-mildew'
]



# Model path
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'ml_models', 'rubber_disease_model.tflite')


# Global interpreter (singleton)
_interpreter = None



def get_interpreter():
    """Load and return the TFLite interpreter"""
    global _interpreter
    
    if _interpreter is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Model file not found at {MODEL_PATH}")
        
        if USE_TF is None or Interpreter is None:
            raise ImportError("Neither tensorflow nor tflite_runtime is installed")
        
        _interpreter = Interpreter(model_path=MODEL_PATH)
        _interpreter.allocate_tensors()
        print(f"✅ Disease detection model loaded from {MODEL_PATH}")
    
    return _interpreter



def preprocess_image(image_base64):
    """Preprocess the image for model input"""
    image_data = base64.b64decode(image_base64)
    image = Image.open(BytesIO(image_data))
    
    original_size = f"{image.width}x{image.height}"
    
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Check if image contains enough green (leaf-like characteristic)
    green_percentage = check_green_content(image)
    
    image = image.resize((224, 224), Image.Resampling.LANCZOS)
    img_array = np.array(image, dtype=np.uint8)
    img_array = np.expand_dims(img_array, axis=0)
    
    return img_array, original_size, green_percentage


def check_green_content(image):
    """Check if the image has enough green pixels (leaf characteristic)"""
    img_array = np.array(image)
    
    # Convert to HSV for better green detection
    # Green in HSV: H between 60-180, S > 20%, V > 20%
    r = img_array[:, :, 0].astype(float)
    g = img_array[:, :, 1].astype(float)
    b = img_array[:, :, 2].astype(float)
    
    # Simple green detection: G > R and G > B
    green_mask = (g > r * 1.1) & (g > b * 1.1) & (g > 30)
    
    total_pixels = img_array.shape[0] * img_array.shape[1]
    green_pixels = np.sum(green_mask)
    green_percentage = (green_pixels / total_pixels) * 100
    
    return round(green_percentage, 2)



@csrf_exempt
@require_POST
def detect_disease(request):
    """API endpoint for disease detection"""
    start_time = time.time()
    image_size = ""
    
    try:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON in request body'
            }, status=400)
        
        image_base64 = data.get('image')
        
        if not image_base64:
            return JsonResponse({
                'success': False,
                'error': 'No image provided'
            }, status=400)
        
        if 'base64,' in image_base64:
            image_base64 = image_base64.split('base64,')[1]
        
        try:
            input_data, image_size, green_percentage = preprocess_image(image_base64)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Failed to process image: {str(e)}'
            }, status=400)
        
        try:
            interpreter = get_interpreter()
        except (FileNotFoundError, ImportError) as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
        
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()
        
        interpreter.set_tensor(input_details[0]['index'], input_data)
        interpreter.invoke()
        output_data = interpreter.get_tensor(output_details[0]['index'])
        
        raw_predictions = output_data[0].astype(float)
        
        if raw_predictions.max() > 1:
            predictions = (raw_predictions / 255.0) * 100
        else:
            predictions = raw_predictions * 100
        
        all_predictions = [
            {'label': label, 'confidence': round(float(conf), 2)}
            for label, conf in zip(DISEASE_LABELS, predictions)
        ]
        all_predictions.sort(key=lambda x: x['confidence'], reverse=True)
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # Two-stage validation
        top_prediction = all_predictions[0]
        
        # Stage 1: Check if image contains leaf-like green pixels
        if green_percentage < MIN_GREEN_PERCENTAGE:
            detected_label = 'Not a Rubber Leaf'
            confidence = 0.0
            is_valid_detection = False
            rejection_reason = f'Insufficient green content ({green_percentage}% green pixels, need {MIN_GREEN_PERCENTAGE}%)'
        # Stage 2: Check if confidence is above threshold
        elif top_prediction['confidence'] < CONFIDENCE_THRESHOLD:
            detected_label = 'Unknown Object'
            confidence = top_prediction['confidence']
            is_valid_detection = False
            rejection_reason = f'Low confidence ({confidence}%, need {CONFIDENCE_THRESHOLD}%)'
        else:
            detected_label = top_prediction['label']
            confidence = top_prediction['confidence']
            is_valid_detection = True
            rejection_reason = None
        
        DiseaseDetectionLog.objects.create(
            disease_detected=detected_label,
            confidence=confidence if is_valid_detection else top_prediction['confidence'],
            image_size=image_size,
            processing_time_ms=processing_time_ms,
            success=True
        )
        
        response_data = {
            'success': True,
            'label': detected_label,
            'confidence': confidence if is_valid_detection else top_prediction['confidence'],
            'isValidDetection': is_valid_detection,
            'greenPercentage': green_percentage,
            'threshold': CONFIDENCE_THRESHOLD,
            'allPredictions': all_predictions,
            'processingTimeMs': processing_time_ms
        }
        
        if rejection_reason:
            response_data['rejectionReason'] = rejection_reason
        
        return JsonResponse(response_data)
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        error_msg = f'{type(e).__name__}: {str(e)}'
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        DiseaseDetectionLog.objects.create(
            disease_detected='Error',
            confidence=0,
            image_size=image_size,
            processing_time_ms=processing_time_ms,
            success=False,
            error_message=f'{error_msg}\n\n{error_trace}'
        )
        
        return JsonResponse({
            'success': False,
            'error': error_msg
        }, status=500)



@require_GET
def disease_health_check(request):
    """Health check endpoint"""
    try:
        model_exists = os.path.exists(MODEL_PATH)
        
        if not model_exists:
            return JsonResponse({
                'status': 'unhealthy',
                'model_loaded': False,
                'error': f'Model file not found at {MODEL_PATH}',
                'disease_labels': DISEASE_LABELS
            }, status=500)
        
        interpreter = get_interpreter()
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()
        
        return JsonResponse({
            'status': 'healthy',
            'model_loaded': True,
            'input_shape': input_details[0]['shape'].tolist(),
            'output_shape': output_details[0]['shape'].tolist(),
            'disease_labels': DISEASE_LABELS,
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'model_loaded': False,
            'error': str(e)
        }, status=500)



@require_GET
def disease_labels(request):
    """Get list of disease labels"""
    return JsonResponse({
        'success': True,
        'labels': DISEASE_LABELS,
        'count': len(DISEASE_LABELS)
    })
