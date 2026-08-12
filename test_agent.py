from parse import extract_text
from structure_extraction import extract_skills, extract_experience_years, extract_education
from scoring import compute_text_similarity, score_candidate

def test_extract_text():
    text = extract_text("resumes/Amit_Desai.txt")
    assert len(text) > 0
    print("test_extract_text passed")

def test_extract_skills():
    sample = "I have experience with Python, AWS, and Docker."
    skills = extract_skills(sample)
    assert "Python" in skills
    assert "AWS" in skills
    print("test_extract_skills passed")

def test_extract_experience():
    sample = "I have 7 years of professional experience."
    years = extract_experience_years(sample)
    assert years == 7.0
    print("test_extract_experience passed")

def test_extract_education():
    sample = "Bachelor of Technology in Computer Science, IIT Roorkee, 2018"
    label, rank = extract_education(sample)
    assert rank == 3
    print("test_extract_education passed")

def test_scoring():
    jd_skills = {"Python", "AWS", "Docker"}
    candidate = {"skills": ["Python", "AWS"], "experience_years": 5.0, "education_rank": 3}
    result = score_candidate(jd_skills, candidate, text_sim=0.5)
    assert 0 <= result["final_score"] <= 100
    print("test_scoring passed")

if __name__ == "__main__":
    test_extract_text()
    test_extract_skills()
    test_extract_experience()
    test_extract_education()
    test_scoring()
    print("\nAll tests passed!")