mini_diff = 0.1;

hdd_height = 15;
hdd_count = 7;

space_around = 8;

hole_diameter = 3;
item_thickness = 2;
item_width = 10;

strip_length = hdd_height * hdd_count + space_around * (hdd_count + 1);

echo(strip_length);

difference() {
    cube([strip_length, item_width, item_thickness], center = false);

    for (i = [0 : hdd_count - 1]) {
        translate([
            space_around + hdd_height / 2 + i * (hdd_height + space_around),
            item_width / 2,
           -mini_diff
        ])
        cylinder(d = hole_diameter,
                 h = item_thickness + 2 * mini_diff,
                 $fn = 24);
    }
}
