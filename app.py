import os
import json
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List

from dotenv import load_dotenv
import streamlit as st
from streamlit_ace import st_ace
from streamlit_autorefresh import st_autorefresh

# Load environment variables BEFORE importing services that read env
load_dotenv(override=False)

from src.utils.ui import render_header, render_subheader, animate_lesson_loading
from src.utils.file_ingest import ingest_uploaded_files
from src.services.lesson_planner import generate_lesson_plan
from src.services.code_evaluator import evaluate_code_guidance
from src.services.chroma_store import get_knowledge_store, upsert_learned_concept
from src.services.ollama_client import quick_answer
from src.services.course_service import (
    generate_course_structure,
    save_course_to_storage,
    expand_lesson_plan
)
from src.services.voice_service import speech_to_text, text_to_speech
from src.utils.reporting import save_concept_report


def init_session_state() -> None:
    defaults = {
        "page": "home",
        "cs_view": "root",
        "lesson_plan": None,
        "learning_objective": None,
        "concept_map": None,
        "code_language": "Python",
        "code_content": "",
        "last_guidance": None,
        "last_evaluated_at": None,
        "chat_history": [],
        "uploaded_context": "",

    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def set_page(page_name: str) -> None:
    st.session_state["page"] = page_name


def set_cs_view(view_name: str) -> None:
    st.session_state["cs_view"] = view_name


def navigate_home() -> None:
    set_page("home")
    set_cs_view("root")


def render_home() -> None:
    render_header("Learning Assistant with Integrated Code Editor")
    st.write("Choose a domain to get started. Only Computer Science is functional right now.")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Learn Computer Science", use_container_width=True):
            set_page("cs")
    with col2:
        st.button("Learn Languages (coming soon)", use_container_width=True, disabled=True)
    with col3:
        st.button("Learn Physics (coming soon)", use_container_width=True, disabled=True)


def render_cs_root() -> None:
    render_header("Computer Science")
    render_subheader("How would you like to learn?")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Learn a New Concept", use_container_width=True):
            set_cs_view("new_concept")
    with col2:
        if st.button("Take a Course", use_container_width=True):
            set_cs_view("course_prompt")

    if st.button("Back to Home", type="secondary"):
        navigate_home()


def render_new_concept_prompt() -> None:
    render_header("Learn a New Concept")
    prompt = st.text_area("What do you want to learn?", placeholder="e.g., Understand pointers in C and how they relate to linked lists")
    uploaded_files = st.file_uploader(
        "Optional: Upload supporting files (PDF, TXT, MD)", type=["pdf", "txt", "md"], accept_multiple_files=True
    )

    if st.button("Generate Lesson Plan", type="primary", use_container_width=True):
        if not prompt.strip():
            st.warning("Please enter what you want to learn.")
            return

        # Ingest files
        with st.spinner("Ingesting uploaded files..."):
            uploaded_context = ingest_uploaded_files(uploaded_files)
            st.session_state["uploaded_context"] = uploaded_context

        # Generate lesson plan with animation of JSON "thinking"
        placeholder = st.empty()
        with placeholder.container():
            animate_lesson_loading("Loading Code Editor and Lesson Plan")

        store = get_knowledge_store()
        lesson_plan = generate_lesson_plan(
            user_request=prompt,
            uploaded_context=st.session_state["uploaded_context"],
            knowledge_store=store,
        )

        # Replace animation with the streamed JSON reveal
        placeholder.empty()
        animate_lesson_loading(
            title="Loading Code Editor and Lesson Plan",
            final_content=json.dumps(lesson_plan, indent=2)[:4000],
            min_cycles=10,
        )

        st.session_state["lesson_plan"] = lesson_plan
        st.session_state["learning_objective"] = lesson_plan.get("objective")
        st.session_state["concept_map"] = lesson_plan.get("concept_map") or lesson_plan.get("milestones")
        set_cs_view("editor")

    if st.button("Back", type="secondary"):
        set_cs_view("root")


def ace_language_from_choice(choice: str) -> str:
    mapping = {
        "Python": "python",
        "C": "c_cpp",
        "C++": "c_cpp",
    }
    return mapping.get(choice, "python")


def render_course_prompt():
    """Render the course generation prompt with course selection"""
    st.title("🎓 Take a Course")
    
    # Check for existing courses
    from src.services.course_storage import CourseStorage
    course_storage = CourseStorage()
    existing_courses = course_storage.list_courses()
    
    if existing_courses:
        st.subheader("📚 Existing Courses")
        selected_course = st.selectbox(
            "Choose an existing course to continue:",
            options=existing_courses,
            index=0,
            format_func=lambda x: x.replace("_", " ").title()
        )
        
        if st.button("📖 Load Course", type="primary"):
            course_data = course_storage.get_course_structure(selected_course)
            if course_data:
                st.session_state["course_structure"] = course_data
                st.session_state["course_user_id"] = "default"
                set_cs_view("course_map")
                st.rerun()
            else:
                st.error("Failed to load course data")
        
        st.divider()
    
    st.subheader("🚀 Generate New Course")
    user_id = st.text_input("User ID (optional):", value="default")
    topic = st.text_input("Enter a topic for your course:", placeholder="e.g., Python Programming, Machine Learning, Web Development")
    
    # Add test connection button
    if st.button("🔍 Test AI Connection", type="secondary"):
        with st.spinner("Testing connection to AI model..."):
            from src.services.course_service import _test_ai_connection
            if _test_ai_connection():
                st.success("✅ AI connection successful! Your ngrok server is working.")
            else:
                st.error("❌ AI connection failed. Check your ngrok server and model.")
    
    # Add debug button to see raw AI response
    if st.button("🐛 Debug AI Response", type="secondary"):
        with st.spinner("Testing AI response generation..."):
            from src.services.ollama_client import call_model
            test_prompt = "Create a simple course structure for 'Python Basics' with 2 sections, each with 2 subsections, each with 2 concepts. Return ONLY valid JSON."
            try:
                response = call_model([
                    {"role": "system", "content": "Return ONLY valid JSON."},
                    {"role": "user", "content": test_prompt}
                ])
                st.text_area("Raw AI Response:", response, height=200)
                st.json({"response_length": len(response), "preview": response[:500]})
            except Exception as e:
                st.error(f"Debug failed: {str(e)}")
    
    # Add debug button to show session state
    if st.button("🔍 Show Session State", type="secondary"):
        st.json({
            "course_structure_exists": "course_structure" in st.session_state,
            "course_user_id": st.session_state.get("course_user_id", "Not set"),
            "current_page": st.session_state.get("page", "Not set"),
            "current_cs_view": st.session_state.get("cs_view", "Not set")
        })
    
    if st.button("Generate Course", type="primary"):
        if not topic.strip():
            st.warning("Please enter a topic.")
            return
            
        # Clear old course data
        if "course_structure" in st.session_state:
            del st.session_state["course_structure"]
        if "course_user_id" in st.session_state:
            del st.session_state["course_user_id"]
            
        with st.spinner("Generating course structure (7x10x10)..."):
            course = generate_course_structure(user_id=user_id, topic=topic)
            
            # Debug output
            st.info(f"📊 Generated course structure:")
            st.json({
                "course_name": course.get("course", "Unknown"),
                "sections_count": len(course.get("sections", [])),
                "first_section": course.get("sections", [{}])[0].get("name", "None") if course.get("sections") else "None",
                "structure_type": "AI Generated" if "sections" in course and len(course["sections"]) > 0 else "Mock Data"
            })
            
        st.session_state["course_structure"] = course
        st.session_state["course_user_id"] = user_id
        set_cs_view("course_map")
    if st.button("Back", type="secondary"):
        set_cs_view("root")


def render_course_map():
    """Render the interactive course map with detailed lesson plans"""
    if "course_structure" not in st.session_state:
        st.error("No course structure found. Please generate a course first.")
        return
    
    course = st.session_state["course_structure"]
    course_name = course.get("course", "Unknown Course")
    
    # Get course progress from storage
    from src.services.course_storage import CourseStorage
    course_storage = CourseStorage()
    progress = course_storage.get_course_progress(course_name)
    
    st.title(f"📚 {course_name} - Course Map")
    
    # Show course metadata
    try:
        course_dir = course_storage.base_dir / course_storage._safe_name(course_name)
        if course_dir.exists():
            course_structure_file = course_dir / "course_structure.json"
            if course_structure_file.exists():
                with open(course_structure_file, "r") as f:
                    course_data = json.load(f)
                    created_at = course_data.get("created_at", "Unknown")
                    if created_at != "Unknown":
                        try:
                            from datetime import datetime
                            created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                            st.caption(f"📅 Course created: {created_dt.strftime('%Y-%m-%d %H:%M')}")
                        except:
                            st.caption(f"📅 Course created: {created_at}")
    except Exception as e:
        pass  # Ignore errors in metadata display
    
    # Show progress summary
    if "error" not in progress:
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Total Lessons", progress["total_lessons"])
        with col2:
            st.metric("Completed", progress["completed_lessons"])
        with col3:
            st.metric("Progress", f"{progress['completion_percentage']:.1f}%")
        with col4:
            total_hours = progress.get("total_time_minutes", 0) / 60
            st.metric("Total Time", f"{total_hours:.1f} hours")
        with col5:
            if progress["completed_lessons"] > 0:
                avg_time = progress.get("total_time_minutes", 0) / progress["completed_lessons"]
                st.metric("Avg/Lesson", f"{avg_time:.1f} min")
            else:
                st.metric("Avg/Lesson", "N/A")
        
        # Add estimated time remaining
        if progress["completed_lessons"] > 0 and progress["total_lessons"] > progress["completed_lessons"]:
            avg_time = progress.get("total_time_minutes", 0) / progress["completed_lessons"]
            remaining_lessons = progress["total_lessons"] - progress["completed_lessons"]
            estimated_remaining = avg_time * remaining_lessons
            st.info(f"⏱️ Estimated time remaining: {estimated_remaining:.1f} minutes ({estimated_remaining/60:.1f} hours)")
    
    # Course structure using tabs for modules
    sections = course.get("sections", [])
    
    if sections:
        # Create tabs for each module
        module_tabs = st.tabs([f"📖 Module {i+1}: {s['name']}" for i, s in enumerate(sections)])
        
        for section_idx, (section, tab) in enumerate(zip(sections, module_tabs)):
            with tab:
                subsections = section.get("subsections", [])
                
                # Use columns to show subsections
                for sub_idx, subsection in enumerate(subsections):
                    st.subheader(f"📝 Submodule {sub_idx + 1}: {subsection['name']}")
                    
                    concepts = subsection.get("concepts", [])
                    
                    # Display concepts in a grid
                    for concept_idx, concept in enumerate(concepts):
                        # Check if detailed plan exists
                        detailed_plan = course_storage.get_detailed_lesson_plan(
                            course_name, section_idx + 1, sub_idx + 1, concept_idx + 1
                        )
                        
                        # Create a unique key for this lesson
                        lesson_key = f"lesson_{section_idx}_{sub_idx}_{concept_idx}"
                        
                        # Check lesson status
                        from src.services.course_storage import CourseStorage
                        course_storage = CourseStorage()
                        is_completed = course_storage.is_lesson_completed(
                            course_name, section_idx + 1, sub_idx + 1, concept_idx + 1
                        )
                        has_saved_code = course_storage.get_lesson_code(
                            course_name, section_idx + 1, sub_idx + 1, concept_idx + 1
                        ) is not None
                        
                        # Get completion time if completed
                        completion_time = None
                        last_code_update = None
                        time_spent = None
                        if is_completed:
                            lesson_dir = course_storage._get_lesson_directory(
                                course_name, section_idx + 1, sub_idx + 1, concept_idx + 1
                            )
                            if lesson_dir:
                                concept_info_file = lesson_dir / "concept_info.json"
                                if concept_info_file.exists():
                                    with open(concept_info_file, "r") as f:
                                        concept_info = json.load(f)
                                        completion_time = concept_info.get("completed_at")
                                        last_code_update = concept_info.get("last_code_update")
                                        time_spent = concept_info.get("total_time_minutes")
                        elif has_saved_code:
                            lesson_dir = course_storage._get_lesson_directory(
                                course_name, section_idx + 1, sub_idx + 1, concept_idx + 1
                            )
                            if lesson_dir:
                                concept_info_file = lesson_dir / "concept_info.json"
                                if concept_info_file.exists():
                                    with open(concept_info_file, "r") as f:
                                        concept_info = json.load(f)
                                        last_code_update = concept_info.get("last_code_update")
                                        time_spent = concept_info.get("total_time_minutes")
                        
                        # Determine status icon and color
                        if is_completed:
                            status_icon = "✅"
                            status_color = "success"
                        elif has_saved_code:
                            status_icon = "🔄"
                            status_color = "warning"
                        else:
                            status_icon = "⏳"
                            status_color = "info"
                        
                        # Create an expander for each concept
                        with st.expander(f"{status_icon} **{concept_idx + 1}. {concept['name']}** - {concept['agenda']}", expanded=False):
                            col1, col2 = st.columns([4, 1])
                            
                            with col1:
                                st.write(f"**Agenda:** {concept['agenda']}")
                                
                                # Show completion time if completed
                                if completion_time:
                                    try:
                                        from datetime import datetime
                                        completion_dt = datetime.fromisoformat(completion_time.replace('Z', '+00:00'))
                                        st.success(f"✅ Completed on {completion_dt.strftime('%Y-%m-%d %H:%M')}")
                                    except:
                                        st.success(f"✅ Completed")
                                
                                # Show last code update time if available
                                if last_code_update:
                                    try:
                                        from datetime import datetime
                                        update_dt = datetime.fromisoformat(last_code_update.replace('Z', '+00:00'))
                                        st.info(f"💻 Last updated: {update_dt.strftime('%Y-%m-%d %H:%M')}")
                                    except:
                                        st.info(f"💻 Has saved code")
                                
                                # Show time spent if available
                                if time_spent:
                                    st.info(f"⏱️ Time spent: {time_spent} minutes")
                                
                                # Show detailed plan if it exists
                                if detailed_plan:
                                    st.markdown("---")
                                    st.markdown("**📋 Detailed Lesson Plan:**")
                                    st.markdown(detailed_plan)
                                    
                                    # Show YouTube videos if they exist
                                    youtube_videos = course_storage.get_youtube_videos(
                                        course_name, section_idx + 1, sub_idx + 1, concept_idx + 1
                                    )
                                    if youtube_videos:
                                        st.markdown("---")
                                        st.markdown("**🎬 Related YouTube Videos:**")
                                        for i, video in enumerate(youtube_videos, 1):
                                            st.markdown(f"**📺 Video {i}: {video.get('title', 'Unknown Title')}**")
                                            st.markdown(f"**Channel:** {video.get('channel', 'Unknown')}")
                                            st.markdown(f"**URL:** [{video.get('url', '#')}]({video.get('url', '#')})")
                                            
                                            # Show AI explanation if available
                                            if video.get('explanation'):
                                                st.markdown("**🤖 Why This Video is Relevant:**")
                                                st.markdown(video.get('explanation'))
                                            
                                            st.markdown("**📝 Summary:**")
                                            st.markdown(video.get('summary', 'No summary available'))
                                            
                                            if i < len(youtube_videos):
                                                st.divider()
                                else:
                                    st.info("No detailed lesson plan yet. Click 'Expand Lesson' to generate one.")
                                
                                # Check if lesson has saved code (in progress)
                                from src.services.course_storage import CourseStorage
                                course_storage = CourseStorage()
                                has_saved_code = course_storage.get_lesson_code(
                                    course_name, section_idx + 1, sub_idx + 1, concept_idx + 1
                                ) is not None
                                
                                # Add Start/Continue Lesson button
                                button_text = "🔄 Continue Lesson" if has_saved_code else "🎯 Start Lesson"
                                button_type = "secondary" if has_saved_code else "primary"
                                
                                if st.button(button_text, key=f"start_lesson_{lesson_key}", type=button_type):
                                    # Set the current lesson context
                                    st.session_state["current_lesson"] = {
                                        "course_name": course_name,
                                        "module_idx": section_idx + 1,
                                        "submodule_idx": sub_idx + 1,
                                        "lesson_idx": concept_idx + 1,
                                        "module_name": section["name"],
                                        "submodule_name": subsection["name"],
                                        "lesson_name": concept["name"],
                                        "agenda": concept["agenda"],
                                        "detailed_plan": detailed_plan
                                    }
                                    set_cs_view("lesson_workspace")
                                    st.rerun()
                            
                            with col2:
                                if not detailed_plan:
                                    if st.button(f"🚀 Expand", key=f"expand_{lesson_key}"):
                                        with st.spinner("Generating detailed lesson plan..."):
                                            try:
                                                detailed_plan = expand_lesson_plan(
                                                    course_name, section_idx + 1, sub_idx + 1, concept_idx + 1
                                                )
                                                if detailed_plan and not detailed_plan.startswith("Error"):
                                                    st.success("✅ Lesson plan expanded!")
                                                    st.rerun()
                                                else:
                                                    st.error(f"Failed to expand: {detailed_plan}")
                                            except Exception as e:
                                                st.error(f"Error during expansion: {str(e)}")
                                else:
                                    st.success("✅ Completed")
                                    
                                    # Add View Code button for completed lessons
                                    if st.button(f"💻 View Code", key=f"view_code_{lesson_key}"):
                                        from src.services.course_storage import CourseStorage
                                        course_storage = CourseStorage()
                                        saved_code = course_storage.get_lesson_code(
                                            course_name, section_idx + 1, sub_idx + 1, concept_idx + 1
                                        )
                                        if saved_code:
                                            st.code(saved_code, language="python")
                                        else:
                                            st.info("No code saved for this lesson yet.")
                                    
                                    if st.button(f"🔄 Regenerate", key=f"regenerate_{lesson_key}"):
                                        with st.spinner("Regenerating detailed lesson plan..."):
                                            try:
                                                detailed_plan = expand_lesson_plan(
                                                    course_name, section_idx + 1, sub_idx + 1, concept_idx + 1
                                                )
                                                if detailed_plan and not detailed_plan.startswith("Error"):
                                                    st.success("✅ Lesson plan regenerated!")
                                                    st.rerun()
                                                else:
                                                    st.error(f"Failed to regenerate: {detailed_plan}")
                                            except Exception as e:
                                                st.error(f"Error during regeneration: {str(e)}")
                        
                        # Add some spacing between concepts
                        if concept_idx < len(concepts) - 1:
                            st.divider()
                    
                    # Add spacing between subsections
                    if sub_idx < len(subsections) - 1:
                        st.markdown("---")
    
    # Add course management options
    st.divider()
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🔄 Refresh Progress"):
            st.rerun()
    
    with col2:
        if st.button("📊 Export Progress"):
            st.json(progress)
    
    with col3:
        if st.button("🏠 Back to Course Selection"):
            set_cs_view("course_prompt")
    
    with col4:
        if st.button("🐛 Debug Course"):
            st.subheader("🔍 Course Debug Information")
            
            # Show course structure info
            st.write("**Course Structure:**")
            st.json({
                "course_name": course_name,
                "total_sections": len(sections),
                "first_section_name": sections[0]["name"] if sections else "None",
                "first_subsection_name": sections[0]["subsections"][0]["name"] if sections and sections[0]["subsections"] else "None",
                "first_concept_name": sections[0]["subsections"][0]["concepts"][0]["name"] if sections and sections[0]["subsections"] and sections[0]["subsections"][0]["concepts"] else "None"
            })
            
            # Show storage info
            st.write("**Storage Information:**")
            try:
                # Test getting a lesson agenda
                test_agenda = course_storage.get_lesson_agenda(course_name, 1, 1, 1)
                st.write(f"Test Lesson Agenda (1,1,1): {test_agenda[:100] if test_agenda else 'None'}...")
                
                # Test getting detailed plan
                test_plan = course_storage.get_detailed_lesson_plan(course_name, 1, 1, 1)
                st.write(f"Test Detailed Plan (1,1,1): {test_plan[:100] if test_plan else 'None'}...")
                
                # Show course directory structure
                course_dir = course_storage.base_dir / course_storage._safe_name(course_name)
                if course_dir.exists():
                    st.write(f"**Course Directory:** {course_dir}")
                    st.write("**Directory Contents:**")
                    for item in list(course_dir.iterdir())[:5]:  # Show first 5 items
                        st.write(f"  - {item.name}")
                else:
                    st.write("**Course Directory:** Does not exist")
                    
            except Exception as e:
                st.error(f"Debug error: {str(e)}")


def render_lesson_workspace() -> None:
    """Render the interactive lesson workspace with code editor for course lessons"""
    if "current_lesson" not in st.session_state:
        st.error("No lesson selected. Please go back to the course map.")
        if st.button("Back to Course Map"):
            set_cs_view("course_map")
        return
    
    lesson = st.session_state["current_lesson"]
    course_name = lesson["course_name"]
    module_name = lesson["module_name"]
    submodule_name = lesson["submodule_name"]
    lesson_name = lesson["lesson_name"]
    agenda = lesson["agenda"]
    detailed_plan = lesson.get("detailed_plan")
    
    # Auto refresh every 20 seconds to trigger re-evaluation
    _ = st_autorefresh(interval=20000, key="auto_refresh_lesson_workspace")
    
    # Header with breadcrumb navigation
    st.title(f"🎯 {lesson_name}")
    st.caption(f"📚 {course_name} → 📖 {module_name} → 📝 {submodule_name}")
    
    # Three-column layout as specified: left (1/3), center (2/3), right (guidance)
    left_col, center_col, right_col = st.columns([1, 2, 1])
    
    with left_col:
        # Top half: Concept map/problem statement with learning objective
        st.markdown("### 🎯 Learning Objective")
        st.write(agenda)
        
        if detailed_plan:
            with st.expander("📖 Detailed Lesson Plan", expanded=True):
                st.markdown(detailed_plan)
                
                # Show YouTube videos if they exist
                youtube_videos = course_storage.get_youtube_videos(
                    course_name,
                    lesson["module_idx"],
                    lesson["submodule_idx"],
                    lesson["lesson_idx"]
                )
                if youtube_videos:
                    st.markdown("---")
                    st.markdown("**🎬 Related YouTube Videos:**")
                    for i, video in enumerate(youtube_videos, 1):
                        st.markdown(f"**📺 Video {i}: {video.get('title', 'Unknown Title')}**")
                        st.markdown(f"**Channel:** {video.get('channel', 'Unknown')}")
                        st.markdown(f"**URL:** [{video.get('url', '#')}]({video.get('url', '#')})")
                        
                        # Show AI explanation if available
                        if video.get('explanation'):
                            st.markdown("**🤖 Why This Video is Relevant:**")
                            st.markdown(video.get('explanation'))
                        
                        st.markdown("**📝 Summary:**")
                        st.markdown(video.get('summary', 'No summary available'))
                        
                        if i < len(youtube_videos):
                            st.divider()
        else:
            st.info("No detailed lesson plan available yet.")
        
        # Bottom half: Chatbox for quick clarifications
        st.markdown("### 💬 Quick Help Chat")
        with st.form("lesson_quick_help"):
            quick_q = st.text_input("Ask a question about this lesson")
            submitted = st.form_submit_button("Ask")
            if submitted and quick_q.strip():
                with st.spinner("Thinking..."):
                    # Use the lesson context for better answers
                    context = f"Course: {course_name}, Module: {module_name}, Submodule: {submodule_name}, Lesson: {lesson_name}, Agenda: {agenda}"
                    if detailed_plan:
                        context += f"\n\nDetailed Plan: {detailed_plan}"
                    
                    answer = quick_answer(quick_q, context=context)
                    st.session_state.setdefault("lesson_chat_history", []).append({"q": quick_q, "a": answer})
        
        # Show chat history
        if st.session_state.get("lesson_chat_history"):
            st.markdown("**Recent Questions:**")
            for idx, turn in enumerate(reversed(st.session_state["lesson_chat_history"][-5:])):  # Show last 5
                st.markdown(f"**Q:** {turn['q']}")
                st.markdown(f"**A:** {turn['a'][:100]}...")
                if idx > 2:  # Limit display
                    break
    
    with center_col:
        st.markdown("### 💻 Code Editor")
        
        # Language selector (C, C++, or Python)
        lang = st.selectbox("Programming Language", ["Python", "C", "C++"], 
                           index=0,  # Default to Python
                           key="lesson_editor_lang")
        
        # Load previously saved code if it exists
        if "lesson_code_content" not in st.session_state:
            from src.services.course_storage import CourseStorage
            course_storage = CourseStorage()
            saved_code = course_storage.get_lesson_code(
                course_name,
                lesson["module_idx"],
                lesson["submodule_idx"],
                lesson["lesson_idx"]
            )
            if saved_code:
                st.session_state["lesson_code_content"] = saved_code
        
        # ST_ACE code editor
        code = st_ace(
            value=st.session_state.get("lesson_code_content", ""),
            language=ace_language_from_choice(lang),
            theme="tomorrow_night",
            height=550,
            show_gutter=True,
            show_print_margin=False,
            wrap=True,
            auto_update=True,
            key="lesson_ace_editor",
        )
        
        if code is not None:
            st.session_state["lesson_code_content"] = code
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💾 Save Progress"):
                # Save the current lesson progress
                from src.services.course_storage import CourseStorage
                course_storage = CourseStorage()
                
                # Mark lesson as completed
                course_storage.mark_lesson_completed(
                    course_name, 
                    lesson["module_idx"], 
                    lesson["submodule_idx"], 
                    lesson["lesson_idx"]
                )
                
                # Save code content
                course_storage.save_lesson_code(
                    course_name,
                    lesson["module_idx"],
                    lesson["submodule_idx"],
                    lesson["lesson_idx"],
                    st.session_state.get("lesson_code_content", "")
                )
                
                st.success("Progress saved!")
        
        with col2:
            if st.button("📊 Show Progress"):
                from src.services.course_storage import CourseStorage
                course_storage = CourseStorage()
                progress = course_storage.get_course_progress(course_name)
                st.json(progress)
        
        with col3:
            if st.button("🔙 Back to Map", type="secondary"):
                set_cs_view("course_map")
                st.rerun()
        

    
    with right_col:
        st.markdown("### 🎯 Guidance Panel")
        
        # Auto-evaluate every 20 seconds
        now = datetime.now(timezone.utc)
        last_eval_iso = st.session_state.get("lesson_last_evaluated_at")
        should_eval = False
        
        if last_eval_iso is None:
            should_eval = True if st.session_state.get("lesson_code_content") else False
        else:
            try:
                last_eval = datetime.fromisoformat(last_eval_iso)
                should_eval = (now - last_eval) >= timedelta(seconds=20)
            except Exception:
                should_eval = True
        
        if should_eval and st.session_state.get("lesson_code_content"):
            with st.spinner("Auto-evaluating your code..."):
                guidance = evaluate_code_guidance(
                    objective=agenda,
                    code=st.session_state.get("lesson_code_content", ""),
                    language=lang,
                )
            st.session_state["lesson_last_guidance"] = guidance
            st.session_state["lesson_last_evaluated_at"] = now.isoformat()
        
        if st.session_state.get("lesson_last_guidance"):
            st.markdown("**💡 Directional Hints (No Solutions):**")
            st.write(st.session_state["lesson_last_guidance"])
        
        # Lesson completion status
        st.markdown("### ✅ Lesson Status")
        from src.services.course_storage import CourseStorage
        course_storage = CourseStorage()
        
        is_completed = course_storage.is_lesson_completed(
            course_name,
            lesson["module_idx"],
            lesson["submodule_idx"],
            lesson["lesson_idx"]
        )
        
        if is_completed:
            st.success("🎉 Lesson Completed!")
        else:
            st.info("📚 Lesson in Progress")
    
        # Voice-based learning evaluation - Always available
    st.divider()
    st.markdown("### 🎤 Voice-Based Learning Check")
    st.caption("Record a verbal summary of what you learned. We'll evaluate your understanding and create a learning pattern.")
    
    # Initialize voice evaluation state
    if "lesson_voice_attempt" not in st.session_state:
        st.session_state["lesson_voice_attempt"] = 1
    if "lesson_voice_transcript" not in st.session_state:
        st.session_state["lesson_voice_transcript"] = ""
    if "lesson_voice_gap_report" not in st.session_state:
        st.session_state["lesson_voice_gap_report"] = None
    if "lesson_voice_final_report" not in st.session_state:
        st.session_state["lesson_voice_final_report"] = None
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        # Always show the recording interface
        st.markdown("**🎤 Live Voice Recording:**")
        
        # Live recording interface using HTML/JavaScript
        recording_html = """
        <div style="text-align: center; padding: 20px; border: 2px solid #e74c3c; border-radius: 10px; background-color: #f8f9fa;">
            <h4>🎤 Live Voice Recording</h4>
            <div id="recording-status" style="margin: 10px 0; font-weight: bold; color: #6c757d;">Ready to record</div>
            <div style="margin: 15px 0;">
                <button id="testMic" onclick="testMicrophone()" style="background-color: #17a2b8; color: white; border: none; padding: 8px 16px; border-radius: 5px; margin: 5px; cursor: pointer; font-size: 12px;">🔍 Test Microphone</button>
                <button id="startRecord" onclick="startRecording()" style="background-color: #e74c3c; color: white; border: none; padding: 10px 20px; border-radius: 5px; margin: 5px; cursor: pointer;">🎤 Start Recording</button>
                <button id="stopRecord" onclick="stopRecording()" style="background-color: #6c757d; color: white; border: none; padding: 10px 20px; border-radius: 5px; margin: 5px; cursor: pointer; display: none;">⏹️ Stop Recording</button>
            </div>
            <div id="audioPlayer" style="margin: 10px 0; display: none;">
                <audio id="recordedAudio" controls style="width: 100%;"></audio>
            </div>
            <div id="downloadSection" style="margin: 10px 0; display: none;">
                <button onclick="downloadAudio()" style="background-color: #28a745; color: white; border: none; padding: 8px 16px; border-radius: 5px; cursor: pointer;">💾 Download Audio</button>
            </div>
        </div>
        
        <script>
        let mediaRecorder;
        let audioChunks = [];
        let audioBlob;
        let testStream;
        
        async function startRecording() {
            try {
                // Check if microphone is available
                if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                    throw new Error('Microphone not supported in this browser');
                }
                
                const stream = await navigator.mediaDevices.getUserMedia({ 
                    audio: {
                        echoCancellation: true,
                        noiseSuppression: true,
                        sampleRate: 44100
                    } 
                });
                
                mediaRecorder = new MediaRecorder(stream, {
                    mimeType: 'audio/webm;codecs=opus'
                });
                audioChunks = [];
                
                mediaRecorder.ondataavailable = (event) => {
                    audioChunks.push(event.data);
                };
                
                mediaRecorder.onstop = () => {
                    audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                    const audioUrl = URL.createObjectURL(audioBlob);
                    document.getElementById('recordedAudio').src = audioUrl;
                    document.getElementById('audioPlayer').style.display = 'block';
                    document.getElementById('downloadSection').style.display = 'block';
                    document.getElementById('recording-status').textContent = '✅ Recording completed!';
                    document.getElementById('recording-status').style.color = '#28a745';
                    
                    // Store the audio blob in session storage for Streamlit
                    const reader = new FileReader();
                    reader.onload = function() {
                        const base64Audio = reader.result.split(',')[1];
                        sessionStorage.setItem('recordedAudio', base64Audio);
                    };
                    reader.readAsDataURL(audioBlob);
                };
                
                mediaRecorder.start();
                document.getElementById('startRecord').style.display = 'none';
                document.getElementById('stopRecord').style.display = 'inline-block';
                document.getElementById('recording-status').textContent = '🎤 Recording...';
                document.getElementById('recording-status').style.color = '#e74c3c';
                
            } catch (error) {
                console.error('Error accessing microphone:', error);
                let errorMessage = '❌ Microphone access denied';
                
                if (error.name === 'NotAllowedError') {
                    errorMessage = '❌ Microphone permission denied. Please allow microphone access in your browser.';
                } else if (error.name === 'NotFoundError') {
                    errorMessage = '❌ No microphone found. Please connect a microphone and try again.';
                } else if (error.name === 'NotSupportedError') {
                    errorMessage = '❌ Microphone not supported in this browser. Please use Chrome, Firefox, or Edge.';
                }
                
                document.getElementById('recording-status').textContent = errorMessage;
                document.getElementById('recording-status').style.color = '#dc3545';
                
                // Show instructions for enabling microphone
                const instructions = document.createElement('div');
                instructions.innerHTML = `
                    <div style="margin-top: 10px; padding: 10px; background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; font-size: 12px;">
                        <strong>How to enable microphone:</strong><br>
                        1. Click the microphone icon in your browser's address bar<br>
                        2. Select "Allow" for microphone access<br>
                        3. Refresh the page and try again<br>
                        <br>
                        <strong>Alternative:</strong> Use the file upload option below
                    </div>
                `;
                document.getElementById('recording-status').parentNode.appendChild(instructions);
            }
        }
        
        function stopRecording() {
            if (mediaRecorder && mediaRecorder.state !== 'inactive') {
                mediaRecorder.stop();
                mediaRecorder.stream.getTracks().forEach(track => track.stop());
                
                document.getElementById('startRecord').style.display = 'inline-block';
                document.getElementById('stopRecord').style.display = 'none';
            }
        }
        
        async function testMicrophone() {
            try {
                document.getElementById('recording-status').textContent = '🔍 Testing microphone...';
                document.getElementById('recording-status').style.color = '#17a2b8';
                
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                testStream = stream;
                
                document.getElementById('recording-status').textContent = '✅ Microphone working! You can now record.';
                document.getElementById('recording-status').style.color = '#28a745';
                
                // Stop the test stream after 2 seconds
                setTimeout(() => {
                    if (testStream) {
                        testStream.getTracks().forEach(track => track.stop());
                        testStream = null;
                    }
                }, 2000);
                
            } catch (error) {
                document.getElementById('recording-status').textContent = '❌ Microphone test failed: ' + error.message;
                document.getElementById('recording-status').style.color = '#dc3545';
            }
        }
        
        function downloadAudio() {
            if (audioBlob) {
                const url = URL.createObjectURL(audioBlob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'recorded_audio.webm';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            }
        }
        </script>
        """
        
        st.components.v1.html(recording_html, height=300)
        
        # Alternative: Simple file upload for recorded audio
        st.markdown("**📁 Upload Recorded Audio (if live recording doesn't work):**")
        uploaded_audio = st.file_uploader(
            "Upload your recorded audio file (WAV, MP3, M4A)",
            type=["wav", "mp3", "m4a"],
            key="lesson_audio_upload"
        )
        
        if uploaded_audio is not None:
            st.session_state["lesson_audio_bytes"] = uploaded_audio.read()
            st.session_state["lesson_audio_ready"] = True
            st.success("✅ Audio uploaded! Click 'Evaluate Summary' to process.")
        
        # Manual transcript option as fallback
        st.markdown("**📝 Or type your summary directly:**")
        manual_transcript = st.text_area(
            "Manual transcript:",
            placeholder="Describe what you learned in this lesson...",
            height=100,
            key="lesson_manual_transcript"
        )
        
        if manual_transcript and len(manual_transcript.strip()) > 10:
            st.session_state["lesson_manual_transcript"] = manual_transcript
            st.session_state["lesson_audio_ready"] = True
            st.success("✅ Manual transcript ready! Click 'Evaluate Summary' to process.")
    
    with col2:
        if st.session_state.get("lesson_audio_ready"):
            st.success("✅ Audio/Transcript ready for evaluation")
        else:
            st.info("Record live audio or upload file")
    
    with col3:
        if st.session_state.get("lesson_audio_ready"):
            if st.button("🔍 Evaluate Summary"):
                with st.spinner("Evaluating your understanding..."):
                    # Handle both audio uploads and manual transcripts
                    from src.services.voice_service import speech_to_text
                    
                    transcript = ""
                    if st.session_state.get("lesson_audio_bytes"):
                        # Convert uploaded audio to text using Eleven Labs STT
                        transcript = speech_to_text(st.session_state["lesson_audio_bytes"])
                        if not transcript.strip():
                            transcript = f"Student provided a voice summary for {lesson_name} lesson but transcript could not be generated."
                    elif st.session_state.get("lesson_manual_transcript"):
                        # Use manual transcript
                        transcript = st.session_state["lesson_manual_transcript"]
                    else:
                        transcript = f"Student provided a summary for {lesson_name} lesson."
                    
                    # Step 2: Send to Ollama via ngrok endpoint for evaluation
                    from src.services.ollama_client import call_model
                    from src.services.code_evaluator import generate_learning_pattern
                    
                    system_prompt = (
                        "You are an expert educator evaluating a student's understanding of a programming concept. "
                        "Analyze the student's verbal summary and provide a structured evaluation with: "
                        "1. Understanding level (excellent/good/fair/needs_improvement) "
                        "2. Specific gaps or misconceptions "
                        "3. Key points that should have been mentioned "
                        "4. Constructive feedback for improvement"
                    )
                    
                    user_prompt = f"""
                    Concept: {lesson_name}
                    Learning Objective: {agenda}
                    Student's Verbal Summary: {transcript}
                    
                    Please evaluate this summary and provide a structured response.
                    """
                    
                    messages = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ]
                    
                    evaluation_response = call_model(messages)
                    
                    # Step 3: Generate spoken feedback using Eleven Labs TTS
                    from src.services.voice_service import text_to_speech
                    spoken_feedback = text_to_speech(evaluation_response[:500])  # Limit for TTS
                    
                    # Store evaluation data
                    st.session_state["lesson_voice_transcript"] = transcript
                    st.session_state["lesson_voice_evaluation"] = evaluation_response
                    st.session_state["lesson_audio_ready"] = False
                    
                    # Display results
                    st.success("Summary evaluated!")
                    st.write("**Transcript:**", transcript)
                    st.write("**AI Evaluation:**", evaluation_response)
                    
                    if spoken_feedback:
                        st.audio(spoken_feedback, format="audio/mp3")
                    
                    # Check if this is first or second attempt
                    if st.session_state["lesson_voice_attempt"] == 1:
                        st.warning("Please record a second attempt to address any gaps identified.")
                        st.session_state["lesson_voice_attempt"] = 2
                        st.session_state["lesson_first_transcript"] = transcript
                        st.session_state["lesson_first_evaluation"] = evaluation_response
                    elif st.session_state["lesson_voice_attempt"] == 2:
                        # Second attempt completed - generate final learning pattern
                        final_learning_pattern = generate_learning_pattern(
                            lesson_name, agenda,
                            st.session_state.get("lesson_first_transcript", ""),
                            st.session_state.get("lesson_first_evaluation", ""),
                            transcript, evaluation_response
                        )
                        
                        # Save to course directory
                        from src.utils.reporting import save_concept_report
                        from src.services.course_storage import CourseStorage
                        course_storage = CourseStorage()
                        course_dir = course_storage._get_lesson_directory(course_name, lesson["module_idx"], lesson["submodule_idx"], lesson["lesson_idx"])
                        
                        if course_dir:
                            final_report = {
                                "concept": lesson_name,
                                "course_name": course_name,
                                "module_name": module_name,
                                "submodule_name": submodule_name,
                                "first_attempt": {
                                    "transcript": st.session_state.get("lesson_first_transcript", ""),
                                    "evaluation": st.session_state.get("lesson_first_evaluation", "")
                                },
                                "second_attempt": {
                                    "transcript": transcript,
                                    "evaluation": evaluation_response
                                },
                                "learning_pattern": final_learning_pattern,
                                "evaluated_at": datetime.now(timezone.utc).isoformat()
                            }
                            
                            report_path = save_concept_report(
                                str(course_dir),
                                course_name,
                                module_name,
                                f"{lesson_name}_voice_evaluation",
                                final_report
                            )
                            st.success(f"Report saved to: {report_path}")
                        
                        # Store 3-line learning pattern in ChromaDB
                        from src.services.chroma_store import upsert_learned_concept
                        upsert_learned_concept(
                            concept=f"{lesson_name} - Learning Patterns",
                            summary=final_learning_pattern
                        )
                        
                        st.success("Learning patterns saved to knowledge base!")
                        
                        # Final spoken summary
                        final_audio = text_to_speech(f"Learning evaluation complete. {final_learning_pattern}")
                        if final_audio:
                            st.audio(final_audio, format="audio/mp3")


def render_course_concept() -> None:
    user_id = st.session_state.get("course_user_id", "demo-user")
    concept = st.session_state.get("current_concept") or {}
    if not concept:
        st.info("No concept selected.")
        if st.button("Back to Course Map"):
            set_cs_view("course_map")
        return

    render_header(f"Concept: {concept.get('name', 'Unnamed')}")

    left_col, center_col, right_col = st.columns([1, 2, 1])

    with left_col:
        st.markdown("### Learning Objective")
        learning_objective = concept.get("agenda", "Learning objective not specified")
        st.write(learning_objective)
        
        # Show concept details
        st.markdown("### Concept Details")
        st.json(concept, expanded=False)

        st.markdown("### Quick Help Chat")
        with st.form("quick_help_course"):
            quick_q = st.text_input("Ask a quick question")
            submitted = st.form_submit_button("Ask")
        if submitted and quick_q.strip():
            with st.spinner("Thinking..."):
                answer = quick_answer(quick_q, context=st.session_state.get("uploaded_context", ""))
            st.session_state.setdefault("course_chat_history", []).append({"q": quick_q, "a": answer})
        for idx, turn in enumerate(reversed(st.session_state.get("course_chat_history", []))):
            st.markdown(f"**You:** {turn['q']}")
            st.markdown(f"**Assistant:** {turn['a']}")
            if idx > 6:
                break

    with center_col:
        st.markdown("### Code Editor")
        lang = st.selectbox("Language", ["Python", "C", "C++"], key="course_editor_lang")
        code = st_ace(
            value=st.session_state.get("course_code_content", ""),
            language=ace_language_from_choice(lang),
            theme="tomorrow_night",
            height=550,
            show_gutter=True,
            show_print_margin=False,
            wrap=True,
            auto_update=True,
            key="course_ace_editor",
        )
        if code is not None:
            st.session_state["course_code_content"] = code

        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("Evaluate Code"):
                with st.spinner("Evaluating code..."):
                    guidance = evaluate_concept_code(
                        user_id=user_id,
                        concept=concept.get("name", ""),
                        student_code=st.session_state.get("course_code_content", ""),
                        topic_hint=st.session_state.get("course_structure", {}).get("course", ""),
                    )
                st.session_state["course_last_guidance"] = guidance
                st.session_state["course_last_eval_at"] = datetime.now(timezone.utc).isoformat()
        with c2:
            if st.button("Back to Map", type="secondary"):
                set_cs_view("course_map")
        with c3:
            st.empty()

    with right_col:
        st.markdown("### Guidance Panel")
        now = datetime.now(timezone.utc)
        last_eval_iso = st.session_state.get("course_last_eval_at")
        should_eval = False
        if last_eval_iso is None:
            should_eval = True if st.session_state.get("course_code_content") else False
        else:
            try:
                last_eval = datetime.fromisoformat(last_eval_iso)
                should_eval = (now - last_eval) >= timedelta(seconds=20)
            except Exception:
                should_eval = True
        if should_eval and st.session_state.get("course_code_content"):
            with st.spinner("Auto-evaluating your code..."):
                guidance = evaluate_code_guidance(
                    user_id=user_id,
                    concept=concept.get("name", ""),
                    student_code=st.session_state.get("course_code_content", ""),
                    topic_hint=st.session_state.get("course_structure", {}).get("course", ""),
                )
            st.session_state["course_last_guidance"] = guidance
            st.session_state["course_last_eval_at"] = now.isoformat()
        if st.session_state.get("course_last_guidance"):
            st.markdown("**Suggestions:**")
            st.write(st.session_state["course_last_guidance"]) 

    st.divider()
    st.markdown("### Voice-Based Concept Evaluation")
    st.caption("Record a short verbal summary. We'll transcribe, evaluate, and optionally speak feedback back to you.")
    
    # Real-time microphone recording instead of file upload
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        st.markdown("**First Attempt**")
        if st.button("🎤 Start Recording", key="start_recording_1", type="primary"):
            st.session_state["recording_1"] = True
            st.session_state["recording_2"] = False
            st.success("Recording started! Click 'Stop Recording' when done.")
        
        if st.button("⏹️ Stop Recording", key="stop_recording_1", type="secondary"):
            if st.session_state.get("recording_1"):
                st.session_state["recording_1"] = False
                # Simulate recording completion
                st.session_state["audio_1_ready"] = True
                st.success("Recording stopped! Click 'Evaluate Summary' to process.")
    
    with col2:
        st.markdown("**Second Attempt**")
        if st.button("🎤 Start Recording", key="start_recording_2", type="primary"):
            st.session_state["recording_2"] = True
            st.session_state["recording_1"] = False
            st.success("Recording started! Click 'Stop Recording' when done.")
        
        if st.button("⏹️ Stop Recording", key="stop_recording_2", type="secondary"):
            if st.session_state.get("recording_2"):
                st.session_state["recording_2"] = False
                # Simulate recording completion
                st.session_state["audio_2_ready"] = True
                st.success("Recording stopped! Click 'Evaluate Summary' to process.")
    
    with col3:
        st.markdown("**Status**")
        if st.session_state.get("recording_1"):
            st.info("🎤 Recording first attempt...")
        elif st.session_state.get("recording_2"):
            st.info("🎤 Recording second attempt...")
        elif st.session_state.get("audio_1_ready"):
            st.success("✅ First recording ready")
        elif st.session_state.get("audio_2_ready"):
            st.success("✅ Second recording ready")
        else:
            st.info("Ready to record")
    
    # First attempt evaluation
    if st.session_state.get("audio_1_ready"):
        if st.button("Evaluate First Summary", key="eval_first"):
            with st.spinner("Transcribing and evaluating..."):
                # Simulate transcript for demo
                transcript = "This is a simulated transcript of the first voice summary for demonstration purposes."
                gap_report = evaluate_summary(
                    user_id=user_id,
                    concept=concept.get("name", ""),
                    student_summary=transcript,
                )
                spoken = text_to_speech(
                    f"Summary evaluation: {gap_report.get('judgement','')}. Key gaps: "
                    + ", ".join(gap_report.get("gaps", [])[:5])
                )
            st.success("First summary evaluated!")
            st.write("**Transcript:**", transcript)
            st.session_state["course_first_summary"] = transcript
            st.session_state["course_first_gap"] = gap_report
            if spoken:
                st.audio(spoken, format="audio/mp3")
            st.session_state["audio_1_ready"] = False

    # Second attempt evaluation
    if st.session_state.get("audio_2_ready"):
        if st.button("Evaluate Second Summary", key="eval_second"):
            with st.spinner("Transcribing and evaluating second attempt..."):
                # Simulate transcript for demo
                transcript2 = "This is a simulated transcript of the second voice summary for demonstration purposes."
                gap_report2 = evaluate_summary(
                    user_id=user_id,
                    concept=concept.get("name", ""),
                    student_summary=transcript2,
                )
                spoken2 = text_to_speech(
                    f"Second evaluation: {gap_report2.get('judgement','')}. Remaining gaps: "
                    + ", ".join(gap_report2.get("gaps", [])[:5])
                )
            st.session_state["course_second_summary"] = transcript2
            st.session_state["course_second_gap"] = gap_report2
            if spoken2:
                st.audio(spoken2, format="audio/mp3")

            # If issues remain, persist a report
            remain = gap_report2.get("gaps") if isinstance(gap_report2, dict) else []
            if remain:
                base_dir = os.getenv("REPORTS_DIR", "./reports")
                path = save_concept_report(
                    base_dir=base_dir,
                    course=st.session_state.get("current_course", "Course"),
                    module=f"{st.session_state.get('current_section','')}/{st.session_state.get('current_subsection','')}",
                    concept=concept.get("name", ""),
                    report={
                        "concept": concept.get("name", ""),
                        "first_summary": st.session_state.get("course_first_summary", ""),
                        "first_gap": st.session_state.get("course_first_gap", {}),
                        "second_summary": transcript2,
                        "second_gap": gap_report2,
                        "learning_style": gap_report2.get("notes", ""),
                    },
                )
                st.info(f"Saved report to {path}")
            st.session_state["audio_2_ready"] = False


def render_editor() -> None:
    render_header("Interactive Coding Workspace")
    lesson_plan = st.session_state.get("lesson_plan") or {}
    learning_objective = st.session_state.get("learning_objective") or "Learning objective not set"

    # Auto refresh every 20 seconds to trigger re-evaluation
    _ = st_autorefresh(interval=20000, key="auto_refresh_editor")

    left_col, center_col, right_col = st.columns([1, 2, 1])

    with left_col:
        st.markdown("### Learning Objective / Concept Map")
        st.write(learning_objective)
        if "concept_map" in st.session_state and st.session_state["concept_map"]:
            with st.expander("Concept Map / Milestones", expanded=True):
                st.json(st.session_state["concept_map"], expanded=False)

        st.markdown("### Quick Help Chat")
        with st.form("quick_help_form"):
            quick_q = st.text_input("Ask a quick question without breaking the flow")
            submitted = st.form_submit_button("Ask")
        if submitted and quick_q.strip():
            with st.spinner("Thinking..."):
                answer = quick_answer(quick_q, context=st.session_state.get("uploaded_context", ""))
            st.session_state["chat_history"].append({"q": quick_q, "a": answer})
        if st.session_state["chat_history"]:
            for idx, turn in enumerate(reversed(st.session_state["chat_history"])):
                st.markdown(f"**You:** {turn['q']}")
                st.markdown(f"**Assistant:** {turn['a']}")
                if idx > 6:
                    break

    with center_col:
        st.markdown("### Code Editor")
        lang = st.selectbox("Language", ["Python", "C", "C++"], index=["Python", "C", "C++"].index(st.session_state["code_language"]))
        st.session_state["code_language"] = lang
        code = st_ace(
            value=st.session_state.get("code_content", ""),
            language=ace_language_from_choice(lang),
            theme="tomorrow_night",
            height=550,                 # optional: approximate 18–40 lines
            show_gutter=True,
            show_print_margin=False,
            wrap=True,
            auto_update=True,
            key="ace_editor",
        )

        if code is not None:
            st.session_state["code_content"] = code

        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("Evaluate Now"):
                with st.spinner("Evaluating your code against the objective..."):
                    guidance = evaluate_code_guidance(
                        objective=learning_objective,
                        code=st.session_state.get("code_content", ""),
                        language=st.session_state.get("code_language", "Python"),
                    )
                st.session_state["last_guidance"] = guidance
                st.session_state["last_evaluated_at"] = datetime.now(timezone.utc).isoformat()
        with c2:
            if st.button("End Session & Save to Knowledge"):
                upsert_learned_concept(
                    concept=learning_objective,
                    summary=lesson_plan.get("summary", ""),
                )
                st.success("Session saved to your knowledge base.")
        with c3:
            if st.button("Back to CS Options", type="secondary"):
                set_cs_view("root")

    with right_col:
        st.markdown("### Guidance Panel")

        # Auto-evaluate every 20 seconds
        now = datetime.now(timezone.utc)
        last_eval_iso = st.session_state.get("last_evaluated_at")
        should_eval = False
        if last_eval_iso is None:
            should_eval = True if st.session_state.get("code_content") else False
        else:
            try:
                last_eval = datetime.fromisoformat(last_eval_iso)
                should_eval = (now - last_eval) >= timedelta(seconds=20)
            except Exception:
                should_eval = True

        if should_eval and st.session_state.get("code_content"):
            with st.spinner("Auto-evaluating your code..."):
                guidance = evaluate_code_guidance(
                    objective=learning_objective,
                    code=st.session_state.get("code_content", ""),
                    language=st.session_state.get("code_language", "Python"),
                )
            st.session_state["last_guidance"] = guidance
            st.session_state["last_evaluated_at"] = now.isoformat()

        if st.session_state.get("last_guidance"):
            st.markdown("**Targeted Suggestions (no solutions):**")
            st.write(st.session_state["last_guidance"])        


def main() -> None:
    st.set_page_config(page_title="Learning Assistant", layout="wide")
    init_session_state()

    # Light custom CSS for aesthetics
    st.markdown(
        """
        <style>
        .stButton>button { height: 3rem; }
        .st-emotion-cache-1kyxreq { padding-top: 0.5rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if st.session_state["page"] == "home":
        render_home()
    elif st.session_state["page"] == "cs":
        if st.session_state["cs_view"] == "root":
            render_cs_root()
        elif st.session_state["cs_view"] == "new_concept":
            render_new_concept_prompt()
        elif st.session_state["cs_view"] == "editor":
            render_editor()
        elif st.session_state["cs_view"] == "course_prompt":
            render_course_prompt()
        elif st.session_state["cs_view"] == "course_map":
            render_course_map()
        elif st.session_state["cs_view"] == "course_concept":
            render_course_concept()
        elif st.session_state["cs_view"] == "lesson_workspace":
            render_lesson_workspace()
        else:
            render_cs_root()
    else:
        render_home()


if __name__ == "__main__":
    main()


