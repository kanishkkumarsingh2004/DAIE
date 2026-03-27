import asyncio
import base64
import cv2
import numpy as np
import os
from daie import Agent, AgentConfig, set_llm
from daie.utils.camera import CameraManager

async def main():
    print("==================================================")
    print("   DAIE VISION CHAT DEMO (Qwen2-VL)              ")
    print("==================================================")
    
    # 1. Configure for Vision Model
    # Note: Ensure you have pulled qwen2-vl:8b in Ollama
    model_name = "qwen3-vl:2b"
    print(f"[*] Initializing with model: {model_name}")
    set_llm(ollama_llm=model_name, stream=True)

    # 2. Setup Agent
    config = AgentConfig(
        name="Vision_AI",
        system_prompt="You are a helpful assistant with vision capabilities. Analyze images from the camera feed accurately.",
        personality="observant, polite, and detailed"
    )
    vision_agent = Agent(config=config)
    
    # 3. Setup Camera
    camera = CameraManager()
    if not camera.initialize_camera():
        print("[!] Error: Could not access camera.")
        return

    print("[+] Camera and AI ready!")
    print("Commands:")
    print(" - 'look' or empty enter: Describe what you see now")
    print(" - 'exit' or 'quit': End session")
    print(" - Any other question: AI will look at camera and answer")

    try:
        while True:
            user_input = input("\nYou: ").strip()
            
            if user_input.lower() in ['exit', 'quit']:
                break
                
            # 'look' is the default behavior if enter is pressed or 'look' is typed
            query = user_input if user_input else "What do you see in this image?"
            
            print("[*] Capturing image...")
            frame = camera.get_frame()
            
            if frame is None:
                print("[!] Error: Failed to capture frame from camera.")
                continue
                
            # Convert frame to base64 for Ollama
            # CameraManager returns RGB, OpenCV needs BGR for encoding
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            _, buffer = cv2.imencode('.jpg', frame_bgr)
            img_base64 = base64.b64encode(buffer).decode('utf-8')
            
            print(f"[*] Analyzing image with {model_name}...")
            print(f"{vision_agent.config.name}: ", end="", flush=True)
            
            # Since Agent.execute_task doesn't take images yet, 
            # we use the underlying LLM direct invoke for this demo
            from daie.core.llm_manager import LLMManager
            llm = LLMManager().get_llm()
            
            # Using the vision-enabled prompt
            response = llm.invoke(query, images=[img_base64])
            
            print() # End of line after response

    finally:
        camera.release()
        print("\n[*] Session closed.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
