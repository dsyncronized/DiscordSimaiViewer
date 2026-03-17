import math
import numpy as np
import imageio
from PIL import Image, ImageDraw
import os

os.environ["IMAGEIO_FFMPEG_EXE"] = "/usr/bin/ffmpeg"

center = (400, 400)
radius = 380
FPS = 30
start_delay = 2.0 # seconds
approach_time = 0.6

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

def create_background():
    img = Image.new("RGB", (800,800), "#20202a")
    draw = ImageDraw.Draw(img)

    draw.ellipse(
        (center[0]-radius, center[1]-radius,
         center[0]+radius, center[1]+radius),
        outline="#c6d0e9",
        width=5
    )

    for lane in range(1,9):
        x,y = lane_to_xy(lane,center,radius)
        draw.ellipse([x-10,y-10,x+10,y+10], fill="#c6d0e9")

    return img

background = create_background()

def draw_frame(frame, chart_data, approach_time):
    img = background.copy()
    draw = ImageDraw.Draw(img)

    current_time = frame / FPS
    
    # this does the start delay
    for event in chart_data:
        note_time = event["time"] + start_delay

        # getting note data (the parser for some reason doesnt have a check for each notes lmao)
        raw_note = event["notes_content_raw"]
        for note in event["notes"]:
            lane = note["start_position"]
            note_type = note.get("note_type")
            hold_time = note.get("hold_time")
            is_break = note.get("is_break")

            # determines when the note starts appearing
            spawn_time = note_time - approach_time
            spawn_radius = 30

            if note_type != "HOLD":
                # checks if note is still on screen, and calculates how far the note is
                if spawn_time <= current_time <= note_time:
                    progress = (current_time - spawn_time) / approach_time
                    progress = max(0.0, min(1.0, progress))

                    # determines where the note should spawn
                    r = spawn_radius + progress * (radius - spawn_radius)

                    x, y = lane_to_xy(lane, center, r)

                    if note_type == "SLIDE":
                        star_points = pentagram_points(x, y, 30)
                        if "/" in raw_note:
                            draw.line(star_points, fill="#ffdf2b", width=7)
                        else:
                            draw.line(star_points, fill="#1e90ff", width=7)

                    elif note_type == "TAP":
                        if "/" in raw_note:
                            draw.ellipse((x-30, y-30, x+30, y+30), outline="#ffdf2b", width=7)
                        else:
                            draw.ellipse((x-30, y-30, x+30, y+30), outline="#ff69b4", width=7)

            elif note_type == "HOLD":
                width = 28
                tip = 28
                head_radius = 30
                tip_push = 12
                hold_end_time = note_time + hold_time

                if spawn_time <= current_time < hold_end_time:

                    # head progress
                    head_progress = (current_time - spawn_time) / approach_time
                    head_progress = max(0.0, min(1.0, head_progress))

                    head_r = spawn_radius + head_progress * (radius - spawn_radius)
                    head_x, head_y = lane_to_xy(lane, center, head_r)

                    # tail progress
                    tail_spawn_time = hold_end_time - approach_time

                    if current_time < tail_spawn_time:
                        tail_progress = 0.0
                    else:
                        tail_progress = (current_time - tail_spawn_time) / approach_time

                    tail_progress = max(0.0, min(1.0, tail_progress))
                    tail_stop = radius - (tip - tip_push)

                    tail_r = spawn_radius + tail_progress * (tail_stop - spawn_radius)
                    tail_r = min(tail_r, radius)
                    tail_x, tail_y = lane_to_xy(lane, center, tail_r)

                    # drawer (drawer, it draws)
                    dx = head_x - tail_x
                    dy = head_y - tail_y
                    length = math.hypot(dx, dy)

                    if length > 0:
                        ux = dx / length
                        uy = dy / length

                        px = -uy
                        py = ux

                        # move tail center backward so the hex doesnt do that sorta thing
                        tail_center_x = tail_x - ux * tip
                        tail_center_y = tail_y - uy * tip

                        # tail geometry
                        tail_tip = (tail_center_x, tail_center_y)
                        tail_base = (
                            tail_center_x + ux * tip,
                            tail_center_y + uy * tip
                        )

                        # head geometry
                        head_tip = (
                            head_x + ux * (head_radius + tip_push),
                            head_y + uy * (head_radius + tip_push)
                        )

                        head_base = (
                            head_tip[0] - ux * tip,
                            head_tip[1] - uy * tip
                        )

                        # yes, more math!
                        points = [
                            tail_tip,
                            (tail_base[0] - px * width, tail_base[1] - py * width),
                            (head_base[0] - px * width, head_base[1] - py * width),
                            head_tip,
                            (head_base[0] + px * width, head_base[1] + py * width),
                            (tail_base[0] + px * width, tail_base[1] + py * width),
                        ]

                        if "/" in raw_note:
                            draw.polygon(points, outline="#ffdf2b", width=6)
                        else:
                            draw.polygon(points, outline="#ff69b4", width=6)
    
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

def render_chart(chart_data, approach_time):
    FPS = 30
    duration = duration = get_chart_duration(chart_data)
    total_frames = int(duration * FPS)

    target_size_mb = 8
    bitrate_mbps = (target_size_mb * 8) / duration  # megabits/sec
    bitrate = f"{bitrate_mbps:.2f}M"

    writer = imageio.get_writer(
        "chart.mp4", # chart slop!
        fps=FPS, # frame slop!
        codec="h264_nvenc", # gpu encoding slop!
        bitrate = bitrate, # bitrate slop!
    )

    for frame in range(total_frames):
        img = draw_frame(frame, chart_data, approach_time)
        writer.append_data(np.array(img))

    writer.close()