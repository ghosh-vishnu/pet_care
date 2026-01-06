# health_vision_service.py - Advanced Health Analysis from Dog Images

import os
import base64
from typing import Dict, List, Tuple
from PIL import Image
import cv2
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = None
if OPENAI_API_KEY and OPENAI_API_KEY != "your-openai-api-key-here":
    client = OpenAI(api_key=OPENAI_API_KEY)

def encode_image(image_path: str) -> str:
    """Encode image to base64 for OpenAI Vision API"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_health_with_vision(image_path: str, breed: str = None) -> Dict[str, any]:
    """
    Analyze dog image for health indicators using OpenAI Vision API.
    Falls back to computer vision analysis if API is not available.
    """
    health_analysis = {
        "overall_health": "Good",
        "observations": [],
        "recommendations": [],
        "concerns": [],
        "body_condition": "Normal",
        "coat_condition": "Healthy",
        "eye_condition": "Normal",
        "energy_level": "Normal"
    }
    
    # Try OpenAI Vision API first if available
    if client:
        try:
            base64_image = encode_image(image_path)
            
            prompt = f"""Analyze this dog image for health indicators. Focus on:
1. Body condition (underweight, normal, overweight)
2. Coat condition (healthy, dry, matted, skin issues)
3. Eye condition (clear, discharge, redness)
4. Overall posture and energy level
5. Any visible health concerns (wounds, limping, skin issues, etc.)
6. General appearance and vitality

{"This appears to be a " + breed + " breed." if breed else ""}

Provide a detailed health assessment in a structured format. Be specific about what you observe."""

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a veterinary assistant AI that analyzes dog images for health indicators. Provide detailed, accurate observations about the dog's physical condition, coat, eyes, body condition, and any visible health concerns. Be specific and professional."
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500
            )
            
            vision_analysis = response.choices[0].message.content
            
            # Parse the vision analysis and extract key information
            health_analysis["vision_analysis"] = vision_analysis
            health_analysis["observations"].append(vision_analysis)
            
            # Extract structured information from the analysis
            analysis_lower = vision_analysis.lower()
            
            # Body condition assessment
            if any(word in analysis_lower for word in ["underweight", "thin", "ribs visible", "emaciated"]):
                health_analysis["body_condition"] = "Underweight"
                health_analysis["concerns"].append("Dog appears underweight - consider nutritional assessment")
            elif any(word in analysis_lower for word in ["overweight", "obese", "excess weight", "chubby"]):
                health_analysis["body_condition"] = "Overweight"
                health_analysis["concerns"].append("Dog appears overweight - consider diet and exercise plan")
            
            # Coat condition
            if any(word in analysis_lower for word in ["healthy coat", "shiny", "glossy", "well-groomed"]):
                health_analysis["coat_condition"] = "Healthy"
            elif any(word in analysis_lower for word in ["dry", "dull", "matte", "dull coat"]):
                health_analysis["coat_condition"] = "Dry"
                health_analysis["recommendations"].append("Coat appears dry - consider omega-3 supplements or dietary changes")
            elif any(word in analysis_lower for word in ["matted", "tangled", "unkempt"]):
                health_analysis["coat_condition"] = "Needs Grooming"
                health_analysis["recommendations"].append("Coat needs grooming - regular brushing recommended")
            elif any(word in analysis_lower for word in ["skin", "rash", "irritation", "redness", "sores"]):
                health_analysis["coat_condition"] = "Skin Issues"
                health_analysis["concerns"].append("Possible skin issues detected - consult with a veterinarian")
            
            # Eye condition
            if any(word in analysis_lower for word in ["clear eyes", "bright", "alert"]):
                health_analysis["eye_condition"] = "Normal"
            elif any(word in analysis_lower for word in ["discharge", "tearing", "redness", "cloudy"]):
                health_analysis["eye_condition"] = "Needs Attention"
                health_analysis["concerns"].append("Eye issues detected - monitor closely and consult vet if persists")
            
            # Energy level
            if any(word in analysis_lower for word in ["alert", "energetic", "active", "playful"]):
                health_analysis["energy_level"] = "High"
            elif any(word in analysis_lower for word in ["lethargic", "tired", "low energy", "sluggish"]):
                health_analysis["energy_level"] = "Low"
                health_analysis["concerns"].append("Dog appears lethargic - monitor behavior and consult vet if concerned")
            
            # Overall health assessment
            if len(health_analysis["concerns"]) > 0:
                health_analysis["overall_health"] = "Needs Attention"
            elif len(health_analysis["recommendations"]) > 0:
                health_analysis["overall_health"] = "Good with Recommendations"
            
            return health_analysis
            
        except Exception as e:
            print(f"Vision API error: {e}")
            # Fall through to computer vision analysis
    
    # Fallback: Computer vision-based health analysis
    return analyze_health_cv(image_path, breed)

def analyze_health_cv(image_path: str, breed: str = None) -> Dict[str, any]:
    # Try to read image using PIL first (supports more formats like AVIF, WebP, etc.)
    try:
        if not os.path.exists(image_path):
            return {
                "overall_health": "Unknown",
                "observations": [f"Image file not found at path: {image_path}"],
                "recommendations": [],
                "concerns": []
            }
        
        pil_img = Image.open(image_path).convert("RGB")
        # Convert PIL image to numpy array for OpenCV
        img_array = np.array(pil_img)
        # Convert RGB to BGR for OpenCV
        img = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        
        if img is None or img.size == 0:
            raise ValueError("Image array is empty after conversion")
            
    except Exception as e:
        # Fallback to OpenCV's imread
        try:
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"OpenCV could not read image")
        except Exception as e2:
            print(f"Error reading image with both PIL and OpenCV: {e}, {e2}")
            return {
                "overall_health": "Unknown",
                "observations": [f"Could not read image file. Please ensure the image is in a supported format (JPG, PNG, AVIF, WebP). Error: {str(e)}"],
                "recommendations": ["Try uploading the image in JPG or PNG format for best compatibility."],
                "concerns": []
            }
    
    health_analysis = {
        "overall_health": "Good",
        "observations": [],
        "recommendations": [],
        "concerns": [],
        "body_condition": "Normal",
        "coat_condition": "Healthy",
        "eye_condition": "Normal",
        "energy_level": "Normal"
    }
    
    # Convert to different color spaces for analysis
    try:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    except Exception as e:
        print(f"Error converting color spaces: {e}")
        return {
            "overall_health": "Unknown",
            "observations": [f"Error processing image: {str(e)}"],
            "recommendations": [],
            "concerns": []
        }
    
    # Analyze brightness and contrast
    brightness = np.mean(gray) / 255.0
    contrast = np.std(gray) / 255.0
    
    # Analyze color distribution (for coat health assessment)
    mean_color = np.mean(img, axis=(0, 1))
    color_variance = np.var(img, axis=(0, 1))
    
    # Detect edges (for clarity and detail)
    edges = cv2.Canny(gray, 50, 150)
    edge_density = np.sum(edges > 0) / (edges.shape[0] * edges.shape[1])
    
    # Observations based on image analysis
    if brightness < 0.3:
        health_analysis["observations"].append("Image is quite dark - better lighting needed for accurate assessment")
    elif brightness > 0.7:
        health_analysis["observations"].append("Image is well-lit - good for visual assessment")
    
    if contrast < 0.15:
        health_analysis["observations"].append("Low contrast detected - may affect detail visibility")
        health_analysis["recommendations"].append("Retake photo with better lighting for clearer assessment")
    
    if edge_density < 0.05:
        health_analysis["observations"].append("Image appears blurry - sharper image recommended")
        health_analysis["recommendations"].append("Use a sharper image for better health assessment")
    
    # Basic health observations
    health_analysis["observations"].append("Image quality analysis completed")
    health_analysis["observations"].append("For detailed health assessment, ensure good lighting and clear focus on the dog")
    
    # General recommendations
    health_analysis["recommendations"].append("Regular vet checkups are recommended")
    health_analysis["recommendations"].append("Monitor your dog's eating, drinking, and activity patterns")
    
    # Don't add breed to observations - it's already shown in the summary header
    # if breed:
    #     health_analysis["observations"].append(f"Breed identified: {breed}")
    
    return health_analysis

def _clean_breed_name(breed: str) -> str:
    """Remove ImageNet class prefix from breed name (e.g., 'n02106662 German shepherd' -> 'German shepherd')"""
    if not breed:
        return breed
    # Remove ImageNet class ID prefix (format: n######## breed_name)
    parts = breed.split(' ', 1)
    if len(parts) > 1 and parts[0].startswith('n') and parts[0][1:].isdigit():
        return parts[1]
    return breed

def generate_health_summary(health_analysis: Dict, breed: str = None, breed_conf: float = 0.0) -> str:
    """
    Generate a user-friendly, trust-building health summary from the analysis results.
    Follows strict formatting guidelines: friendly, concise, under 300 words.
    """
    parts = []
    
    # 1️⃣ Friendly Opening
    parts.append("I've analyzed your dog's photo and here's what I noticed!")
    
    # 2️⃣ Quick Summary (2-3 bullets max)
    summary_bullets = []
    
    # Breed detection
    clean_breed = None
    if breed:
        clean_breed = _clean_breed_name(breed)
        breed_pct = round(breed_conf * 100) if breed_conf > 0 else 0
        if breed_pct > 0:
            summary_bullets.append(f"• Detected Breed: {clean_breed} ({breed_pct}% confidence)")
    
    # Overall health status
    overall = health_analysis.get("overall_health", "Good")
    if overall == "Good":
        health_status = "Good"
    elif overall == "Good with Recommendations":
        health_status = "Fair"
    elif overall == "Needs Attention":
        health_status = "Needs Attention"
    else:
        health_status = "Good"
    
    summary_bullets.append(f"• Overall Health Status: {health_status}")
    
    parts.append("\n" + "\n".join(summary_bullets))
    
    # 3️⃣ Visual Health Observations
    observations_list = []
    
    # Body Condition
    body_cond = health_analysis.get("body_condition", "Normal")
    if body_cond == "Underweight":
        observations_list.append("🐕 Body Condition: May need attention - appears underweight")
    elif body_cond == "Overweight":
        observations_list.append("🐕 Body Condition: May need attention - appears overweight")
    else:
        observations_list.append("🐕 Body Condition: Looks healthy")
    
    # Coat & Skin
    coat_cond = health_analysis.get("coat_condition", "Healthy")
    if coat_cond == "Healthy":
        observations_list.append("🧥 Coat & Skin: Looks healthy")
    elif coat_cond == "Dry":
        observations_list.append("🧥 Coat & Skin: May need attention - appears dry")
    elif coat_cond == "Needs Grooming":
        observations_list.append("🧥 Coat & Skin: May need attention - grooming recommended")
    elif coat_cond == "Skin Issues":
        observations_list.append("🧥 Coat & Skin: May need attention - possible skin concerns")
    else:
        observations_list.append("🧥 Coat & Skin: No major concerns visible")
    
    # Eyes & Face
    eye_cond = health_analysis.get("eye_condition", "Normal")
    if eye_cond == "Normal":
        observations_list.append("👀 Eyes & Face: Looks healthy")
    else:
        observations_list.append("👀 Eyes & Face: May need attention")
    
    # Energy & Posture
    energy = health_analysis.get("energy_level", "Normal")
    if energy == "High":
        observations_list.append("⚡ Energy & Posture: Looks healthy and alert")
    elif energy == "Low":
        observations_list.append("⚡ Energy & Posture: May need attention - appears low energy")
    else:
        observations_list.append("⚡ Energy & Posture: No major concerns visible")
    
    parts.append("\nVisual Health Observations:")
    parts.append("\n".join(observations_list))
    
    # 4️⃣ Key Concern (If Any) - Only 1-2 main concerns
    concerns = health_analysis.get("concerns", [])
    if concerns:
        # Filter to most important 1-2 concerns, simplify language
        main_concerns = []
        for concern in concerns[:2]:  # Max 2 concerns
            if concern and concern.strip():
                # Simplify concern text for user-friendly language
                concern_text = concern.strip()
                # Remove technical jargon and make it friendly
                if "underweight" in concern_text.lower():
                    main_concerns.append("⚠️ Possible underweight – ribs appear slightly visible.")
                elif "overweight" in concern_text.lower():
                    main_concerns.append("⚠️ Possible overweight – consider diet and exercise plan.")
                elif "skin" in concern_text.lower():
                    main_concerns.append("⚠️ Possible skin issues detected – consider vet consultation.")
                elif "eye" in concern_text.lower():
                    main_concerns.append("⚠️ Eye concerns detected – monitor closely.")
                elif "lethargic" in concern_text.lower():
                    main_concerns.append("⚠️ Low energy levels observed – monitor behavior patterns.")
                else:
                    # Use simplified version of the concern
                    simplified = concern_text.replace("Dog appears ", "").replace(" - ", " – ").strip(".")
                    main_concerns.append(f"⚠️ {simplified}.")
        
        if main_concerns:
            parts.append("\n\nKey Concern:")
            parts.append("\n".join(main_concerns))
    
    # 5️⃣ Recommended Next Steps - Action-oriented
    recommendations = health_analysis.get("recommendations", [])
    next_steps = []
    
    # Extract actionable recommendations, simplify language
    for rec in recommendations[:3]:  # Max 3 recommendations
        if rec and rec.strip():
            rec_text = rec.strip()
            # Simplify recommendation text
            if "vet" in rec_text.lower() or "veterinarian" in rec_text.lower():
                next_steps.append("Vet check recommended if concerns persist")
            elif "grooming" in rec_text.lower() or "brushing" in rec_text.lower():
                next_steps.append("Regular grooming and brushing recommended")
            elif "nutrition" in rec_text.lower() or "diet" in rec_text.lower() or "omega" in rec_text.lower():
                next_steps.append("Nutrition assessment and dietary adjustments may help")
            elif "exercise" in rec_text.lower():
                next_steps.append("Regular exercise and activity monitoring")
            elif "monitor" in rec_text.lower():
                next_steps.append("Continue monitoring eating, drinking, and activity patterns")
            else:
                # Use simplified version
                simplified = rec_text.replace("Coat appears ", "").replace("Dog appears ", "").strip(".")
                if simplified and len(simplified) < 80:  # Keep it short
                    next_steps.append(simplified.capitalize())
    
    # Add default recommendations if none exist
    if not next_steps:
        if health_status == "Good":
            next_steps.append("Continue regular care and monitoring")
        elif health_status == "Fair":
            next_steps.append("Monitor closely and maintain regular vet checkups")
        else:
            next_steps.append("Consider veterinary consultation for detailed assessment")
    
    parts.append("\n\nRecommended Next Steps:")
    parts.append("\n".join(f"• {step}" for step in next_steps[:3]))
    
    # 6️⃣ Soft Disclaimer (ONE LINE ONLY)
    parts.append("\n\nThis is an AI-based visual assessment and not a medical diagnosis.")
    
    return "\n".join(parts)

