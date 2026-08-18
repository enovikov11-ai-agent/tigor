$fn = 32;

tolerance=0.25;

d = 4.7 + tolerance;
h = 6.1;
u = 0.05;
sub_h = 2.9 + tolerance;
shaft_d = 20;

plato_h = 5;
plato_d = 100;

union() {
    difference() {
        cylinder(h=h, d=shaft_d);
        
        translate([0, 0, -u]) {
            intersection() {
                cylinder(h=h + 2 * u, d=d);

                translate([0, 0, h / 2 + u]) {
                    cube([d, sub_h, h + 2 * u], center=true);
                }
            }
        }
    }

    translate([0, 0, -plato_h]) {
        cylinder(h=plato_h, d=plato_d);
    }
}
