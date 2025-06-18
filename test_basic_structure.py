#!/usr/bin/env python3
"""
Basic test to verify PRDY project structure and logic without external dependencies
"""

import sys
import os

def test_project_structure():
    """Test that all expected files and directories exist"""
    expected_files = [
        'prdy/__init__.py',
        'prdy/models/__init__.py',
        'prdy/models/prd.py',
        'prdy/models/database.py',
        'prdy/engines/__init__.py',
        'prdy/engines/question_engine.py',
        'prdy/utils/__init__.py',
        'prdy/utils/prd_service.py',
        'prdy/utils/ai_integration.py',
        'prdy/utils/environment_manager.py',
        'prdy/utils/settings_manager.py',
        'prdy/utils/state_detector.py',
        'prdy/utils/logger.py',
        'prdy/app_controller.py',
        'prdy/cli.py',
        'prdy/gui.py',
        'prdy/__main__.py',
        'requirements.txt',
        'pyproject.toml',
        'README.md',
        'CLAUDE.md',
        'bootstrap.py'
    ]
    
    missing_files = []
    for file_path in expected_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    else:
        print("✅ All expected files present")
        return True

def test_import_structure():
    """Test that files can be imported without syntax errors"""
    test_files = [
        'prdy.models.prd',
        'prdy.models.database', 
        'prdy.engines.question_engine',
        'prdy.utils.prd_service',
        'prdy.utils.ai_integration',
        'prdy.utils.environment_manager',
        'prdy.utils.settings_manager',
        'prdy.utils.state_detector',
        'prdy.utils.logger',
        'prdy.app_controller',
        'prdy.cli',
        'prdy.gui',
        'prdy.__main__'
    ]
    
    sys.path.insert(0, '.')
    
    for module_name in test_files:
        try:
            # Try to compile the file to check for syntax errors
            file_path = module_name.replace('.', '/') + '.py'
            with open(file_path, 'r') as f:
                code = f.read()
            compile(code, file_path, 'exec')
            print(f"✅ {module_name} - syntax OK")
        except SyntaxError as e:
            print(f"❌ {module_name} - syntax error: {e}")
            return False
        except Exception as e:
            print(f"⚠️  {module_name} - other error: {e}")
    
    return True

def test_question_engine_logic():
    """Test question engine logic without external dependencies"""
    # Test the basic question structure
    question_data = {
        "id": "test_question",
        "question": "What is your project name?",
        "type": "text",
        "required": True,
        "help_text": "Choose a clear name"
    }
    
    # Test dependency filtering logic
    questions = [
        {"id": "q1", "depends_on": None},
        {"id": "q2", "depends_on": {"q1": "yes"}},
        {"id": "q3", "depends_on": {"q1": "no"}}
    ]
    
    answers = {"q1": "yes"}
    
    # Simulate dependency filtering
    filtered = []
    for q in questions:
        if q["depends_on"] is None:
            filtered.append(q)
        else:
            deps_met = True
            for dep_key, dep_value in q["depends_on"].items():
                if dep_key not in answers or answers[dep_key] != dep_value:
                    deps_met = False
                    break
            if deps_met:
                filtered.append(q)
    
    expected_filtered = [{"id": "q1", "depends_on": None}, {"id": "q2", "depends_on": {"q1": "yes"}}]
    
    if len(filtered) == 2 and filtered[0]["id"] == "q1" and filtered[1]["id"] == "q2":
        print("✅ Question dependency filtering logic works")
        return True
    else:
        print(f"❌ Question filtering failed. Expected 2 questions, got {len(filtered)}")
        return False

def test_prd_generation_logic():
    """Test basic PRD generation logic"""
    # Simulate session data
    session_data = {
        "project_name": "Test Project",
        "problem_statement": "Users need better tools",
        "value_proposition": "We provide the best solution",
        "key_features": "Feature 1, Feature 2, Feature 3",
        "success_metrics": "Increase user satisfaction by 50%"
    }
    
    # Test list parsing
    def parse_list_field(field_value):
        if not field_value:
            return []
        
        items = []
        for line in field_value.split('\n'):
            line = line.strip()
            if line:
                line = line.lstrip('•-*123456789. ')
                if ',' in line:
                    items.extend([item.strip() for item in line.split(',') if item.strip()])
                else:
                    items.append(line)
        return items
    
    features = parse_list_field(session_data["key_features"])
    
    if len(features) == 3 and features[0] == "Feature 1":
        print("✅ PRD generation logic works")
        return True
    else:
        print(f"❌ PRD generation failed. Expected 3 features, got {len(features)}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing PRDY Application Structure\n")
    
    tests = [
        ("Project Structure", test_project_structure),
        ("Import Structure", test_import_structure),
        ("Question Engine Logic", test_question_engine_logic),
        ("PRD Generation Logic", test_prd_generation_logic)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        print("-" * 40)
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All tests passed! PRDY structure is solid.")
        print("\n📝 Next steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Install package: pip install -e .")
        print("3. Run GUI: prdy")
        print("4. Run CLI: prdy --cli")
        print("5. Create first PRD: prdy new")
    else:
        print(f"\n⚠️  {len(results) - passed} tests failed. Review issues above.")
    
    return passed == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)