from moviepy.editor import VideoFileClip
import os


videoClip = VideoFileClip("v.mp4")
videoClip.write_videofile("v.webm")
videoClip = VideoFileClip("v.webm")
os.remove("v.mp4")
videoClip.write_videofile("v.mp4")
