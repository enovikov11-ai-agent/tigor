$fn = 32;

tolerance=0.25;

d = 4.7 + tolerance;
h = 6.1;
u = 0.05;
sub_h = 2.9 + tolerance;
shaft_d = 30;

extra_h = 3;


difference() {
    cylinder(h=extra_h + h, d=shaft_d);
    
    translate([0, 0, -u]) {
        intersection() {
            cylinder(h=h + 2 * u, d=d);

            translate([0, 0, h / 2 + u]) {
                cube([d, sub_h, h + 2 * u], center=true);
            }
        }
    }
    
    difference() {
        translate([-9, -50, h + extra_h - 1 + u]){
            cube([18, 100, 1]);
        }
        
        translate([0.45, 0, 0]) {
            cylinder(h=100, d=5.4);
        }
    }
}

/*
18
d 5.4
6.8
5.9
*/