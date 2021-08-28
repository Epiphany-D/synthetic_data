import copy
import os

import pandas as pd

import label_file


def fitRectangle(gene_BBox):
    gene_BBox = gene_BBox.split(',')  # change str to list
    x = int(gene_BBox[0])
    y = int(gene_BBox[1])
    width = int(gene_BBox[2])
    height = int(gene_BBox[3])
    gene_BBox = [[x, y], [x + width, y], [x + width, y + height],
                 [x, y + height]]
    return gene_BBox


def fitLabel(id, display_text):
    return str(id) + ':gene:' + str(display_text)


def getShapes(element):
    for idx in range(len(element)):
        shape = copy.deepcopy(base_shape)
        shape['ID'] = idx
        shape['points'] = fitRectangle(element['gene_BBox'].iloc[idx])
        shape['label'] = fitLabel(idx, element['display_text'].iloc[idx])
        shapes.append(shape)
    return shapes


if __name__ == "__main__":
    path = 'match_pics/45_all_text.csv'
    im_dir = 'synthetic_json'
    shapes = []
    base_shape = {
        "line_color": None,
        "fill_color": None,
        "component": [],
        "rotated_box": [],
        "ID": None,
        "label": None,
        "points": [],
        "group_id": None,
        "shape_type": "polygon",
        "flags": {}
    }
    data = pd.read_csv(path)
    imgs = data.groupby('fig_name')  # group by picture name

    for img in imgs:
        image_name = img[0]  # the type of img is a tuple
        imageHeight = int(img[1]['height'].iloc[0])  # the type of img[1] is a Series
        imageWidth = int(img[1]['width'].iloc[0])
        shapes = getShapes(img[1])
        output_path = os.path.join(im_dir, image_name.replace('.jpg', '') + ".json")
        template_label_file = label_file.LabelFile()
        template_label_file.save(output_path, shapes, image_name, imageHeight, imageWidth)
        shapes.clear()
