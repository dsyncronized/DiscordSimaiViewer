import math
import numpy as np
import imageio
from PIL import Image, ImageDraw

center = (400, 400)
radius = 380
FPS = 30
start_delay = 2.0 # seconds

# determines lane position
def lane_to_xy(lane, center, radius):
    angle = math.radians((lane - 1) * 45 + 22.5 - 90)
    x = center[0] + radius * math.cos(angle)
    y = center[1] + radius * math.sin(angle)
    return x, y

# uhhhh star idk i cant do math
def pentagram_points(center_x, center_y, radius):
    points = []
    for i in range(5):
        angle = math.radians(90 + i * 72)
        px = center_x + radius * math.cos(angle)
        py = center_y - radius * math.sin(angle)
        points.append((px, py))
    order = [0, 2, 4, 1, 3, 0]
    return [points[i] for i in order]

def draw_frame(frame, chart_data, approach_time=0.7):
    # draw background
    img = Image.new("RGB", (800, 800), "#20202a")
    draw = ImageDraw.Draw(img)

    # draw inner ring
    draw.ellipse(
        (center[0]-radius, center[1]-radius,
         center[0]+radius, center[1]+radius),
        outline="#c6d0e9",
        width=5
    )

    # draw lane dots
    for lane in range(1, 9):
        x, y = lane_to_xy(lane, center, radius)
        draw.ellipse([x-10, y-10, x+10, y+10], fill="#c6d0e9")

    current_time = frame / FPS
    
    # this does the start delay
    for event in chart_data:
        note_time = event["time"] + start_delay

        # getting note data
        for note in event["notes"]:
            lane = note["start_position"]
            note_type = note.get("note_type")
            hold_time = note.get("hold_time")
            is_break = note.get("is_break")

            # determines when the note starts appearing
            spawn_time = note_time - approach_time
            spawn_radius = 30
            hit_radius = radius

            if note_type != "HOLD":
                # checks if note is still on screen, and calculates how far the note is
                if spawn_time <= current_time <= note_time:
                    progress = (current_time - spawn_time) / approach_time
                    progress = max(0.0, min(1.0, progress))

                    # determines where the note should spawn
                    r = spawn_radius + progress * (hit_radius - spawn_radius)

                    x, y = lane_to_xy(lane, center, r)

                    if note_type == "SLIDE":
                        star_points = pentagram_points(x, y, 30)
                        draw.line(star_points, fill="#1e90ff", width=7)
                    elif note_type == "TAP":
                        draw.ellipse((x-30, y-30, x+30, y+30), outline="#ff69b4", width=7)

            elif note_type == "HOLD":
                hold_end_time = note_time + hold_time

                if spawn_time <= current_time <= hold_end_time:

                    # head progress
                    head_progress = (current_time - spawn_time) / approach_time
                    head_progress = max(0.0, min(1.0, head_progress))

                    head_r = spawn_radius + head_progress * (hit_radius - spawn_radius)
                    head_x, head_y = lane_to_xy(lane, center, head_r)

                    draw.ellipse((head_x-30, head_y-30, head_x+30, head_y+30),
                                outline="#ff69b4", width=7)

                    # tail progress
                    tail_spawn_time = hold_end_time - approach_time

                    if current_time < tail_spawn_time:
                        tail_progress = 0.0
                    else:
                        tail_progress = (current_time - tail_spawn_time) / approach_time

                    tail_progress = max(0.0, min(1.0, tail_progress))

                    tail_r = spawn_radius + tail_progress * (hit_radius - spawn_radius)
                    tail_x, tail_y = lane_to_xy(lane, center, tail_r)

                    # drawer (drawer, it draws)
                    draw.line((tail_x, tail_y, head_x, head_y),
                            fill="#32cd32", width=12)

                    draw.ellipse((tail_x-20, tail_y-20, tail_x+20, tail_y+20),
                                outline="#32cd32", width=5)
    
    return img

def get_chart_duration(chart_data):
    latest = 0
    for event in chart_data:
        base_time = event["time"]

        for note in event["notes"]:
            hold_time = note.get("hold_time", 0)
            end_time = base_time + hold_time
            latest = max(latest, end_time)
            
    return latest + start_delay + 2

def render_chart(chart_data, approach_time=0.7):
    FPS = 30
    duration = duration = get_chart_duration(chart_data)
    total_frames = int(duration * FPS)

    writer = imageio.get_writer("chart.mp4", fps=FPS)

    for frame in range(total_frames):
        img = draw_frame(frame, chart_data, approach_time)
        writer.append_data(np.array(img))

    writer.close()