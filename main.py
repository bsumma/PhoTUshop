import tkinter as tk
from tkinter import filedialog
import tkinter.colorchooser as colorchooser
from PIL import Image, ImageTk
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from foundations import *
from filters import *
from restoration import *


class DraggableCanvas(tk.Canvas):
    def __init__(self, *args, **kwargs):
        tk.Canvas.__init__(self, *args, **kwargs)
        self.bind("<ButtonPress-1>", self.start_drag)
        self.bind("<B1-Motion>", self.drag)

        self.start_x = 0
        self.start_y = 0

    def start_drag(self, event):
        self.start_x = event.x
        self.start_y = event.y

    def drag(self, event):
        dx = event.x - self.start_x
        dy = event.y - self.start_y
        self.move("all", dx, dy)
        self.start_x = event.x
        self.start_y = event.y


def donothing():
    print("Doing Nothing")


class TransferFunctionApp:
    def __init__(self, root):
        self.root = root
        self.canvas = None
        self.is_drawing = False
        self.current_line = []

    def start_drawing(self, event):
        self.is_drawing = True
        self.current_line = []

    def draw(self, event):
        if self.is_drawing:
            x = event.x
            y = event.y
            self.current_line.append((x, y))
            self.redraw_line()

    def adjust_polyline(self):
        adjusted_polyline = []
        n = len(self.current_line)
        for i in range(n - 1):
            x1, y1 = self.current_line[i]
            x2, y2 = self.current_line[i + 1]
            dx = x2 - x1
            dy = y2 - y1
            steps = max(abs(dx), abs(dy))
            if steps == 0:
                adjusted_polyline.append((x1, y1))
            else:
                x_step = dx / steps
                y_step = dy / steps
                for step in range(steps):
                    x = round(x1 + step * x_step)
                    y = round(y1 + step * y_step)
                    adjusted_polyline.append((x, y))
        adjusted_polyline.append(self.current_line[-1])
        self.current_line = adjusted_polyline

    def enforce_monotonic(self):
        # Make the line monotonic
        self.adjust_polyline()
        sorted_points = sorted(self.current_line)
        new_line = []
        seen = []
        for i in range(len(self.current_line)):
            current_x, current_y = self.current_line[i]
            if current_x not in seen:
                seen.append(current_x)
                new_line.append((current_x, current_y))
        self.current_line = new_line

        for i in range(255):
            if i not in seen:
                self.current_line.append((i, 255))
        self.current_line = sorted(self.current_line)
        self.redraw_line()

    def redraw_line(self):
        # Clear the canvas
        self.canvas.delete("all")

        # Draw the line
        for i in range(1, len(self.current_line)):
            x1, y1 = self.current_line[i - 1]
            x2, y2 = self.current_line[i]
            self.canvas.create_line(x1, y1, x2, y2)

    def stop_drawing(self, event):
        global image
        if self.is_drawing:
            self.is_drawing = False
            self.enforce_monotonic()
            self.redraw_line()
            self.process_transfer_function()
            image = apply_transfer_function(image, transfer_function)
            update_display()

    def process_transfer_function(self):
        global transfer_function
        transfer_function = np.resize(transfer_function, (256,))
        for i in range(len(self.current_line)):
            current_x, current_y = self.current_line[i]
            if (current_x > 255):
                current_x = 255
            if (current_x < 0):
                current_x = 0
            transfer_function[current_x] = 255 - current_y

    def launch(self):
        top_level = tk.Toplevel(self.root)
        self.canvas = tk.Canvas(top_level, width=255, height=255)
        self.canvas.pack()

        self.canvas.bind("<Button-1>", self.start_drawing)
        self.canvas.bind("<B1-Motion>", self.draw)
        self.canvas.bind("<ButtonRelease-1>", self.stop_drawing)


def display_histogram(hist, bins):
    # Create a new Tkinter window
    window = tk.Toplevel()

    # Create a Figure object and set its size
    fig = Figure(figsize=(6, 4), dpi=100)

    # Add a subplot to the Figure
    ax = fig.add_subplot(111)

    # Plot the histogram
    ax.bar(bins[:-1], hist, width=np.diff(bins), align='edge')

    # Set labels and title
    ax.set_xlabel('Value')
    ax.set_ylabel('Frequency')
    ax.set_title('Histogram')

    # Create a FigureCanvasTkAgg object
    canvas = FigureCanvasTkAgg(fig, master=window)
    canvas.draw()

    # Pack the canvas into the window
    canvas.get_tk_widget().pack()

    # Run the Tkinter event loop
    tk.mainloop()


def open_color_chooser():
    global edit_color

    if 'edit_color' not in globals():
        edit_color = (0, 0, 0)
    solid_button = tk.Button(root, text="Solid Button", command=donothing)
    solid_button.config(bg=edit_color)
    # Open color chooser dialog
    edit_color = colorchooser.askcolor()[0]
    # ignore g and b since we are only dealing in grayscale.


def get_filter_size():
    # Create a new window
    global filter_size
    filter_size = 3

    def fix_odd(value):
        value = int(value)
        if value % 2 == 0:
            value += 1
        scale.set(value)

    def on_close():
        global filter_size
        # Get the final value of the scale bar when the window is closed
        filter_size = int(scale.get())
        scale_window.destroy()

    scale_window = tk.Toplevel(root)
    scale_window.title("Kernel Size")

    # Add a scale bar to the window
    scale_label = tk.Label(scale_window, text="Kernel size")
    scale = tk.Scale(scale_window, from_=3, to=31, orient=tk.HORIZONTAL, command=fix_odd)
    scale_label.pack(padx=5, pady=5)
    scale.pack(padx=5, pady=5)

    scale_window.protocol("WM_DELETE_WINDOW", on_close)
    scale_window.wait_window()
    return filter_size


def open_image():
    file_path = filedialog.askopenfilename()
    global image, original_image, canvas
    if file_path:
        image = Image.open(file_path)
        original_image = image.copy()
        update_display()


def update_display():
    global image, canvas
    photo = ImageTk.PhotoImage(image)
    old_translation = canvas.coords("image_tag")
    canvas.delete("image_tag")
    canvas.create_image(0, 0, anchor='nw', image=photo, tags="image_tag")
    if len(old_translation) > 0:
        canvas.move("image_tag", old_translation[0], old_translation[1])
    # this keeps in in scope, otherwise it won't display
    canvas.photo = photo


def mask_image():
    file_path = filedialog.askopenfilename()
    global image
    if file_path:
        mask_image = Image.open(file_path)
        mask(image, mask_image)
    update_display()


def average_image():
    file_path = filedialog.askopenfilename()
    global image
    if file_path:
        other = Image.open(file_path)
        average(image, other)
    update_display()


def invert_image():
    global image
    image = invert(image)
    update_display()


def apply_gamma():
    global image
    image = gamma_correction(image)
    update_display()


def apply_gaussian():
    global image
    size = get_filter_size()
    print("Filter size:" + str(size))
    image = gaussian_filter(image, size, size / 6.0)
    update_display()


def apply_median():
    global image
    size = get_filter_size()
    print("Filter size:" + str(size))
    image = median(image, size)
    update_display()


def apply_sobel():
    global image


def close_image():
    global image, canvas
    if 'image' in globals():
        image.close()
        canvas.delete("image_tag")


def revert_image():
    global image, original_image, canvas
    image = original_image.copy()
    update_display()


def compute_histogram(num_bins):
    global image
    hist, bins = np.histogram(image, bins=num_bins)
    return hist, bins


def hist_eq():
    global image
    image = histogram_equalization(image)
    update_display()


def launch_app():
    app = TransferFunctionApp(root)
    app.launch()


def compute_and_display_histogram():
    hist, bins = compute_histogram(num_bins=255)
    display_histogram(hist, bins)


root = tk.Tk()
root.geometry("1024x768")
root.title("PhoTUshop")
root.resizable(width=True, height=True)

menubar = tk.Menu(root)

filemenu = tk.Menu(menubar, tearoff=0)
filemenu.add_command(label="Open", command=open_image)
filemenu.add_command(label="Close", command=close_image)
filemenu.add_command(label="Revert", command=revert_image)

filemenu.add_separator()

filemenu.add_command(label="Average Two", command=average_image)
filemenu.add_command(label="Apply Mask", command=mask_image)


filemenu.add_separator()

filemenu.add_command(label="Exit", command=root.quit)
menubar.add_cascade(label="File", menu=filemenu)

intmenu = tk.Menu(menubar, tearoff=0)
intmenu.add_command(label="Draw Color", command=open_color_chooser)
intmenu.add_separator()
intmenu.add_command(label="Invert Image", command=invert_image)
intmenu.add_command(label="Gamma Correction", command=apply_gamma)
intmenu.add_separator()
intmenu.add_command(label="Intensity Transformation", command=launch_app)
intmenu.add_separator()
intmenu.add_command(label="Show Histogram", command=compute_and_display_histogram)
intmenu.add_command(label="Equalize Histogram", command=hist_eq)
menubar.add_cascade(label="Intensity", menu=intmenu)

filtermenu = tk.Menu(menubar, tearoff=0)

noiseSUBmenu = tk.Menu(filtermenu, tearoff=0)
filterSUBmenu = tk.Menu(filtermenu, tearoff=0)

noiseSUBmenu.add_command(label="Gaussian", command=donothing)
noiseSUBmenu.add_command(label="Raliegh", command=donothing)
noiseSUBmenu.add_command(label="Gamma", command=donothing)
noiseSUBmenu.add_command(label="Uniform", command=donothing)
noiseSUBmenu.add_command(label="Salt and Pepper", command=donothing)

filterSUBmenu.add_command(label="Gaussian", command=apply_gaussian)
filterSUBmenu.add_command(label="Sobel", command=apply_sobel)
filterSUBmenu.add_command(label="Canny", command=donothing)
filterSUBmenu.add_separator()
filterSUBmenu.add_command(label="Arithmetic Mean", command=donothing)
filterSUBmenu.add_command(label="Geometric Mean", command=donothing)
filterSUBmenu.add_command(label="Harmonic Mean", command=donothing)
filterSUBmenu.add_command(label="Contraharmonic Mean", command=donothing)
filterSUBmenu.add_command(label="Max", command=donothing)
filterSUBmenu.add_command(label="Min", command=donothing)
filterSUBmenu.add_command(label="Midpoint", command=donothing)
filterSUBmenu.add_command(label="Alpha Trimmed", command=donothing)
filterSUBmenu.add_command(label="Adaptive Median", command=donothing)
filterSUBmenu.add_command(label="Bilateral", command=donothing)
filterSUBmenu.add_command(label="Guided", command=donothing)
filterSUBmenu.add_command(label="Joint Bilateral", command=donothing)

filtermenu.add_cascade(label="Add Noise", menu=noiseSUBmenu)
filtermenu.add_cascade(label="Apply Filter", menu=filterSUBmenu)
menubar.add_cascade(label="Filters", menu=filtermenu)

filtermenu = tk.Menu(menubar, tearoff=0)
filtermenu.add_command(label="Display Fourier Transform", command=donothing)
filtermenu.add_command(label="Apply Frequency Domain Filter", command=donothing)
menubar.add_cascade(label="Frequency", menu=filtermenu)

waveletmenu = tk.Menu(menubar, tearoff=0)
waveletmenu.add_command(label="Display Wavelet Decomposition", command=donothing)
waveletmenu.add_command(label="Produce Progressive Reconstruction", command=donothing)
menubar.add_cascade(label="Wavelets", menu=waveletmenu)


compressmenu = tk.Menu(menubar, tearoff=0)

losslessmenu = tk.Menu(compressmenu, tearoff=0)
losslessmenu.add_command(label="Huffman", command=donothing)
losslessmenu.add_command(label="Predictive", command=donothing)

lossymenu = tk.Menu(compressmenu, tearoff=0)
lossymenu.add_command(label="Quantize", command=donothing)
lossymenu.add_command(label="JPEG", command=donothing)
lossymenu.add_command(label="JPEG 2000", command=donothing)


compressmenu.add_cascade(label="Lossless", menu=losslessmenu)
compressmenu.add_cascade(label="Lossy", menu=lossymenu)
menubar.add_cascade(label="Compression", menu=compressmenu)

morphmenu = tk.Menu(menubar, tearoff=0)
morphmenu.add_command(label="Dilate", command=donothing)
morphmenu.add_command(label="Erode", command=donothing)
morphmenu.add_command(label="Connected Components", command=donothing)
morphmenu.add_command(label="Reconstruction", command=donothing)

menubar.add_cascade(label="Morphological", menu=morphmenu)

segmenu = tk.Menu(menubar, tearoff=0)
segmenu.add_command(label="Hough", command=donothing)
segmenu.add_command(label="Watershed", command=donothing)
segmenu.add_command(label="Superpixels", command=donothing)
segmenu.add_command(label="Gabor", command=donothing)
segmenu.add_command(label="Watershed", command=donothing)
segmenu.add_command(label="Graph Cuts", command=donothing)
segmenu.add_command(label="Active Contours", command=donothing)
segmenu.add_command(label="Level Sets", command=donothing)
segmenu.add_command(label="Live Wire ", command=donothing)

menubar.add_cascade(label="Segmentation", menu=segmenu)

featuremenu = tk.Menu(menubar, tearoff=0)
featuremenu.add_command(label="Harris", command=donothing)
featuremenu.add_command(label="MSER", command=donothing)
featuremenu.add_command(label="SURF", command=donothing)
featuremenu.add_command(label="SIFT", command=donothing)

menubar.add_cascade(label="Features", menu=featuremenu)

registrationmenu = tk.Menu(menubar, tearoff=0)
registrationmenu.add_command(label="Pairwise", command=donothing)
menubar.add_cascade(label="Registration", menu=registrationmenu)

menubar.add_cascade(label="Deep Learning", menu=filtermenu)

root.config(menu=menubar)

canvas = DraggableCanvas(root, width=2048, height=2048, bg="white")
canvas.pack()

image = Image.new('L', (0, 0))
original_image = Image.new('L', (0, 0))

transfer_function = []

root.mainloop()
