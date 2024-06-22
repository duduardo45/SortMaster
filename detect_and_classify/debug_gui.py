import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from opencv_feat_match import match_features, register_exemplar
from PIL import Image, ImageTk

output_filename = "output/processed_image.jpg"


def update_image(panel, image, max_size=(800, 600)):
    image = Image.fromarray(image)
    image.thumbnail(max_size)
    image = ImageTk.PhotoImage(image)
    panel.config(image=image)
    panel.image = image


def browse_file(entry):
    filename = filedialog.askopenfilename(
        filetypes=[("All files", "*.*"), ("Image files", "*.jpg;*.jpeg;*.png")]
    )
    entry.delete(0, tk.END)
    entry.insert(0, filename)


def process_images(exemplar_path, scene_path, nfeatures, ratio_test_threshold, panel):
    try:
        exemplar_image, exemplar_keypoints, exemplar_descriptors = register_exemplar(
            exemplar_path, nfeatures
        )
        result_image, _ = match_features(
            exemplar_image,
            exemplar_keypoints,
            exemplar_descriptors,
            scene_path,
            nfeatures,
            ratio_test_threshold,
            output_filename,
        )
        if result_image is not None:
            update_image(panel, result_image)
        else:
            messagebox.showinfo(
                "Result", "Not enough matches found to compute homography."
            )
    except Exception as e:
        messagebox.showerror("Error", str(e))


def on_slider_release(
    event, exemplar_entry, scene_entry, nfeatures_slider, ratio_slider, image_panel
):
    process_images(
        exemplar_entry.get(),
        scene_entry.get(),
        int(nfeatures_slider.get()),
        float(ratio_slider.get()),
        image_panel,
    )


def setup_gui(root):
    initial_nfeatures = 5000
    initial_ratio_test_threshold = 0.7

    # Create frames
    frame = ttk.Frame(root, padding=10)
    frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    # Exemplar image
    ttk.Label(frame, text="Exemplar Image:").grid(row=0, column=0, sticky=tk.W)
    exemplar_entry = ttk.Entry(frame, width=40)
    exemplar_entry.grid(row=0, column=1)
    ttk.Button(frame, text="Browse", command=lambda: browse_file(exemplar_entry)).grid(
        row=0, column=2
    )

    # Scene image
    ttk.Label(frame, text="Scene Image:").grid(row=1, column=0, sticky=tk.W)
    scene_entry = ttk.Entry(frame, width=40)
    scene_entry.grid(row=1, column=1)
    ttk.Button(frame, text="Browse", command=lambda: browse_file(scene_entry)).grid(
        row=1, column=2
    )

    # ORB parameters
    ttk.Label(frame, text="Number of Features:").grid(row=2, column=0, sticky=tk.W)
    nfeatures_slider = ttk.Scale(frame, from_=500, to_=100000, orient="horizontal")
    nfeatures_slider.set(initial_nfeatures)
    nfeatures_slider.grid(row=2, column=1, sticky=(tk.W, tk.E))

    # Ratio test threshold
    ttk.Label(frame, text="Ratio Test Threshold:").grid(row=3, column=0, sticky=tk.W)
    ratio_slider = ttk.Scale(frame, from_=0.0, to_=1.0, orient="horizontal")
    ratio_slider.set(initial_ratio_test_threshold)
    ratio_slider.grid(row=3, column=1, sticky=(tk.W, tk.E))

    # Create StringVar for both sliders
    nfeatures_var = tk.StringVar()
    ratio_var = tk.StringVar()

    # Update StringVar whenever the slider value changes
    def update_nfeatures_var(value):
        nfeatures_var.set(f"{int(float(value))}")

    def update_ratio_var(value):
        ratio_var.set(f"{float(value):.2f}")

    # Bind the update functions to the sliders
    nfeatures_slider.config(command=update_nfeatures_var)
    ratio_slider.config(command=update_ratio_var)

    # Add labels next to the sliders to display their current values
    ttk.Label(frame, textvariable=nfeatures_var).grid(row=2, column=2, sticky=tk.W)
    ttk.Label(frame, textvariable=ratio_var).grid(row=3, column=2, sticky=tk.W)

    # Initialize the StringVar with the default slider values
    nfeatures_var.set(f"{int(nfeatures_slider.get())}")
    ratio_var.set(f"{ratio_slider.get():.2f}")

    # Bind the slider release event to the processing function
    nfeatures_slider.bind(
        "<ButtonRelease-1>",
        lambda event: on_slider_release(
            event,
            exemplar_entry,
            scene_entry,
            nfeatures_slider,
            ratio_slider,
            image_panel,
        ),
    )
    ratio_slider.bind(
        "<ButtonRelease-1>",
        lambda event: on_slider_release(
            event,
            exemplar_entry,
            scene_entry,
            nfeatures_slider,
            ratio_slider,
            image_panel,
        ),
    )

    # Image display panel
    global image_panel
    image_panel = ttk.Label(frame)
    image_panel.grid(row=5, column=0, columnspan=3)


def main():
    # Create the main window
    root = tk.Tk()
    root.title("Image Matching Debugger")

    # Setup the GUI
    setup_gui(root)

    # Run the application
    root.mainloop()


if __name__ == "__main__":
    main()
