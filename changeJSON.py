import json
import os


def rec2pol(points):
    x1 = round(points[0][0], 2)
    y1 = round(points[0][1], 2)
    x2 = round(points[1][0], 2)
    y2 = round(points[1][1], 2)
    points = [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
    return points


filePath = 'val'
for path in os.listdir(filePath):
    if '.json' in path:
        path = os.path.join(filePath, path)
        with open(path, 'rb') as f:
            params = json.load(f)
            for dic in params['shapes']:
                points = dic["points"]
                label = dic["label"]
                if ':gene:' in dic['label']:
                    try:
                        id = dic['ID']
                    except:
                        dic.clear()
                        dic.update({
                            "line_color": None,
                            "fill_color": None,
                            "component": [],
                            "rotated_box": [],
                            "ID": id + 1,
                            "label": label,
                            "points": rec2pol(points),
                            "group_id": None,
                            "shape_type": "polygon",
                            "flags": {}
                        })
                else:
                    if 'line_color' not in dic.keys():
                        id += 1
                        dic.clear()
                        dic.update({
                            "line_color": None,
                            "fill_color": None,
                            "component": [],
                            "rotated_box": [],
                            "ID": id,
                            "label": label,
                            "points": rec2pol(points),
                            "group_id": None,
                            "shape_type": "polygon",
                            "flags": {}
                        })
        with open(path, 'w') as f:
            json.dump(params, f)
    else:
        continue
