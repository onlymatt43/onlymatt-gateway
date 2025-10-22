#!/usr/bin/env python3
"""
Test script for website analysis and generation
"""
import asyncio
import httpx
import json

async def test_website_analysis():
    """Test website analysis endpoint"""
    base_url = "http://localhost:8000"

    # Test website analysis
    payload = {
        "url": "https://www.apple.com"
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            headers = {
                'x-om-key': 'sk_admin_e0e7fbda4b440ad82606c940d6fa084f',
                'Content-Type': 'application/json'
            }
            response = await client.post(
                f"{base_url}/ai/website/analyze",
                json=payload,
                headers=headers
            )

            print(f"Analysis Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print("Analysis successful!")
                print(f"Title: {result['analysis']['title']}")
                print(f"Content Type: {result['analysis']['content_type']}")
                print(f"Has Header: {result['analysis']['structure']['has_header']}")
            else:
                print(f"Analysis failed: {response.text}")

    except Exception as e:
        print(f"Error: {e}")

async def test_website_generation():
    """Test website generation endpoint"""
    base_url = "http://localhost:8000"

    # Test data for website generation
    payload = {
        "site_data": {
            "name": "Ma Société Tech",
            "industry": "technology",
            "audience": "startups",
            "description": "Solutions innovantes pour entreprises modernes",
            "services": ["Développement web", "IA", "Cloud"],
            "contact": {
                "email": "contact@masociete.com",
                "phone": "+33 1 23 45 67 89"
            }
        },
        "references": ["https://www.apple.com", "https://www.google.com"],
        "template": "modern",
                "target_platform": "wordpress",  # Tester le déploiement WordPress avec vraies credentials
        "wordpress_config": {
            "url": "https://om43.com",
            "username": "om43onepm",  # Vrai username WordPress
            "application_password": "EffJMIGP6xOPozjFJS(3e@63"  # Mot de passe admin réel
        }
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            headers = {
                'x-om-key': 'sk_admin_e0e7fbda4b440ad82606c940d6fa084f',
                'Content-Type': 'application/json'
            }
            response = await client.post(
                f"{base_url}/ai/website/generate",
                json=payload,
                headers=headers
            )

            print(f"\nGeneration Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print("Website generation successful!")
                print(f"Target Platform: {result['target_platform']}")
                if 'wordpress_deployment' in result['website']:
                    print("WordPress deployment included")
                else:
                    print("Content generated for manual deployment")
            else:
                print(f"Generation failed: {response.text}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Testing website analysis and generation...")
    asyncio.run(test_website_analysis())
    asyncio.run(test_website_generation())