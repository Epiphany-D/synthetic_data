import os

import cv2
import pandas as pd
from matching_name import matching_name


def mat_elements(gene_name, img_name, id):
    truth_img = read(truth_ele_path, fig_name)
    for img in truth_img:
        if matching_name(img[0], gene_name) == 'OK':
            for idx in range(len(img[1][truth_ele_gene_name])):
                if img[1][truth_ele_gene_name].iloc[idx] == gene_name:
                    return True, str(id) + ':' + gene_name + '\n'
                else:
                    continue
        else:
            continue
    return False, ""


def mat_relations(img_name, relation, startor, receptor, id):
    truth_img = read(truth_rel_path, fig_name)
    for img in truth_img:
        if img[0] == img_name:
            for idx in range(len(img[1][truth_rel_name])):
                if img[1][truth_rel_name].iloc[idx] == relation and img[1][truth_rel_s].iloc[idx] == startor and \
                        img[1][truth_rel_r].iloc[idx] == receptor:
                    return str(id) + ':' + relation + ':' + startor + '|' + receptor + '\n'
                elif img[1][truth_rel_name].iloc[idx] == relation and (img[1][truth_rel_s].iloc[idx] == startor or \
                                                                       img[1][truth_rel_r].iloc[idx] == receptor):
                    return str(id) + ':' + relation + ':' + img[1][truth_rel_s].iloc[
                        idx] + '|' + img[1][truth_rel_r].iloc[idx] + '(not match perfectly)' + '\n'
                else:
                    continue
        else:
            continue
    return str(id) + ':' + '\n'


def read(path, name):
    data = pd.read_csv(path)
    imgs = data.groupby(name)  # group by picture name
    return imgs


def rect(points):
    points = points.split(',')  # change str to list
    x = int(float(points[0]))
    y = int(float(points[1]))
    width = int(float(points[2]))
    height = int(float(points[3]))
    return (x, y), (x + width, y + height), (x + width + 3, y - 5)


def f1():
    val_imgs = read(val_ele_path, fig_name)
    for img in val_imgs:
        img_name = img[0]
        fname = os.path.join(img_path, img_name)
        cv_img = cv2.imread(fname)
        output_path = 'match_pics/' + img_name.replace(".jpg", "")

        try:
            os.mkdir(output_path)
        except:
            pass

        with open(os.path.join(output_path, 'gt_element.txt'), mode='w') as g:
            with open(os.path.join(output_path, 'val_element.txt'), mode='w') as f:
                for idx in range(len(img[1][val_ele_points])):
                    pt1, pt2, txt_plc = rect(img[1][val_ele_points].iloc[idx])
                    cv2.rectangle(cv_img, pt1, pt2, (255, 0, 0), 2)
                    cv2.putText(cv_img, str(idx), txt_plc, cv2.FONT_HERSHEY_PLAIN, 1, (255, 0, 0), 2)
                    gene_name = img[1][val_ele_gene_name].iloc[idx]
                    try:
                        g.write(mat_elements(gene_name, img_name, idx))
                    except:
                        print(img_name + " has invaild chars:" + str(idx) + ':' + gene_name + " in gt ele")
                    try:
                        f.write(str(idx) + ':' + gene_name + '\n')
                    except:
                        print(img_name + " has invaild chars:" + str(idx) + ':' + gene_name + " in val ele")
        cv2.imwrite(os.path.join(output_path, 'tmp' + img_name), cv_img)


def f2():
    val_imgs = read(val_rel_path, fig_name)

    for img in val_imgs:

        val_activate = []
        val_inhibit = []

        img_name = img[0]
        output_path = 'match_pics/' + img_name.replace(".jpg", "")
        fname = os.path.join(output_path, 'tmp' + img_name)
        cv_img = cv2.imread(fname)

        for idx in range(len(img[1][val_rel_points])):
            if 'activate' in img[1][val_rel_name].iloc[idx]:
                val_activate.append({'points': img[1][val_rel_points].iloc[idx],
                                     'startor': img[1][val_rel_s].iloc[idx],
                                     'receptor': img[1][val_rel_r].iloc[idx]})
            else:
                val_inhibit.append({'points': img[1][val_rel_points].iloc[idx],
                                    'startor': img[1][val_rel_s].iloc[idx],
                                    'receptor': img[1][val_rel_r].iloc[idx]})

        with open(os.path.join(output_path, 'gt_relation.txt'), mode='w') as g:
            with open(os.path.join(output_path, 'val_relation.txt'), mode='w') as f:
                f.write("activate:\n".title())
                g.write("activate:\n".title())
                for idx in range(len(val_activate)):
                    pt1, pt2, txt_plc = rect(val_activate[idx]['points'])
                    cv2.rectangle(cv_img, pt1, pt2, (0, 240, 0), 2)
                    cv2.putText(cv_img, str(idx), txt_plc, cv2.FONT_HERSHEY_PLAIN, 1, (0, 240, 0), 2)
                    s = val_activate[idx]['startor']
                    r = val_activate[idx]['receptor']
                    try:
                        g.write(mat_relations(img_name, 'activate_relation', s, r, idx))
                    except:
                        print(img_name + " has invaild chars:" + str(idx) + ':' + s + '|' + r + ' in gt ac')
                    try:
                        f.write(str(idx) + ':activate:' + s + '|' + r + '\n')
                    except:
                        print(img_name + " has invaild chars:" + str(idx) + ':' + s + '|' + r + ' in val ac')

                f.write("inhibit:\n".title())
                g.write("inhibit:\n".title())
                for idx in range(len(val_inhibit)):
                    pt1, pt2, txt_plc = rect(val_inhibit[idx]['points'])
                    cv2.rectangle(cv_img, pt1, pt2, (0, 0, 240), 2)
                    cv2.putText(cv_img, str(idx), txt_plc, cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 240), 2)
                    s = val_inhibit[idx]['startor']
                    r = val_inhibit[idx]['receptor']
                    try:
                        g.write(mat_relations(img_name, 'inhibit_relation', s, r, idx))
                    except:
                        print(img_name + " has invaild chars:" + str(idx) + ':' + s + '|' + r + ' in gt inhi')
                    try:
                        f.write(str(idx) + ':inhibit:' + s + '|' + r + '\n')
                    except:
                        print(img_name + " has invaild chars:" + str(idx) + ':' + s + '|' + r + ' in val inhi')
        cv2.imwrite(os.path.join(output_path, img_name), cv_img)
        os.remove(os.path.join(output_path, 'tmp' + img_name))


def main():
    f1()
    f2()


img_path = 'val'
fig_name = 'fig_name'

val_ele_path = 'match_pics/validation model outputs elements.csv'
val_ele_points = 'coordinates'
val_ele_gene_name = 'gene_name'

truth_ele_path = 'match_pics/45_all_text.csv'
truth_ele_gene_name = 'display_text'

val_rel_path = 'match_pics/validation model outputs relation.csv'
val_rel_points = 'bbox'
val_rel_name = 'category_id'
val_rel_s = 'startor'
val_rel_r = 'receptor'

truth_rel_path = 'match_pics/45_all_text_relation.csv'
truth_rel_points = 'gene_BBox'
truth_rel_gene_name = 'display_text'
truth_rel_name = 'relation_type'
truth_rel_s = 'activator'
truth_rel_r = 'receptor'

main()
