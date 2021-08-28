import os

import cv2
import pandas as pd


def mat_elements(gene_name, img_name, id):
    truth_img = read(truth_ele_path, fig_name)
    for img in truth_img:
        if img[0] == img_name:
            for idx in range(len(img[1][truth_ele_gene_name])):
                if img[1][truth_ele_gene_name].iloc[idx] == gene_name:
                    return str(id) + ':' + gene_name + '\n'
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
                        f.write(str(idx) + ':' + gene_name + '\n')
                    except:
                        print(img_name + " has invaild chars:" + str(idx) + ':' + gene_name)
        cv2.imwrite(os.path.join(output_path, 'tmp' + img_name), cv_img)


def f2():
    val_imgs = read(val_rls_path, fig_name)
    for img in val_imgs:
        val_activate = []
        val_inhibit = []
        img_name = img[0]
        output_path = 'match_pics/' + img_name.replace(".jpg", "")
        fname = os.path.join(output_path, 'tmp' + img_name)
        cv_img = cv2.imread(fname)
        for idx in range(len(img[1][val_rls_points])):
            if 'activate' in img[1][val_rls_name].iloc[idx]:
                val_activate.append(img[1][val_rls_points].iloc[idx])
            else:
                val_inhibit.append(img[1][val_rls_points].iloc[idx])
        with open(os.path.join(output_path, 'gt_relation.txt'), mode='w') as g:
            with open(os.path.join(output_path, 'val_relation.txt'), mode='w') as f:
                for idx in range(len(val_activate)):
                    pt1, pt2, txt_plc = rect(val_activate[idx])
                    cv2.rectangle(cv_img, pt1, pt2, (0, 240, 0), 2)
                    cv2.putText(cv_img, str(idx), txt_plc, cv2.FONT_HERSHEY_PLAIN, 1, (0, 240, 0), 2)
                    # g.write(mat_relations(gene_name, img_name, idx))
                    f.write(str(idx) + ':activate' + '\n')
                for idx in range(len(val_inhibit)):
                    pt1, pt2, txt_plc = rect(val_inhibit[idx])
                    cv2.rectangle(cv_img, pt1, pt2, (0, 0, 240), 2)
                    cv2.putText(cv_img, str(idx), txt_plc, cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 240), 2)
                    # g.write(mat_relations(gene_name, img_name, idx))
                    f.write(str(idx) + ':inhibit' + '\n')
        cv2.imwrite(os.path.join(output_path, img_name), cv_img)
        os.remove(os.path.join(output_path, 'tmp' + img_name))


def main():
    try:
        f1()
    except:
        pass
    finally:
        f2()


img_path = 'val'
fig_name = 'fig_name'

val_ele_path = 'match_pics/validation model outputs elements.csv'
val_ele_points = 'coordinates'
val_ele_gene_name = 'gene_name'

truth_ele_path = 'match_pics/45_all_text.csv'
truth_ele_points = 'gene_BBox'
truth_ele_gene_name = 'display_text'

val_rls_path = 'match_pics/validation model outputs relation.csv'
val_rls_points = 'bbox'
val_rls_name = 'category_id'

main()
