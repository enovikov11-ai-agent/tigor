import gi, os, signal, datetime
gi.require_version("Gst", "1.0")
from gi.repository import Gst, GLib

OUT_DIR = "/var/www/html"

PIPELINE = (
    "libcamerasrc ! "
    "video/x-raw,format=NV12,width=1920,height=1080,framerate=30/1 ! "
    "v4l2h264enc extra-controls=\"encode,repeat_sequence_header=1\" ! "
    "h264parse config-interval=1 ! "
    "mpegtsmux alignment=7 name=mux ! "
    "queue leaky=downstream max-size-buffers=400 ! "
    "appsink name=sink emit-signals=true drop=true sync=false"
)

Gst.init(None)
pipeline = Gst.parse_launch(PIPELINE)
appsink  = pipeline.get_by_name("sink")


os.makedirs(OUT_DIR, exist_ok=True)
current_fp          = None        # open file handle for current segment
segment_start_ts_ns = None        # PTS at which current segment started
nanosec_per_seg     = 4_000_000_000


def _new_filename():
    now = datetime.datetime.utcnow()
    return now.strftime("%Y-%m-%d-%H-%M-%S.ts")

def _rotate_segment(pts_ns):
    global current_fp, segment_start_ts_ns
    if current_fp:
        current_fp.close()
    segment_start_ts_ns = pts_ns
    path = os.path.join(OUT_DIR, _new_filename())
    current_fp = open(path, "wb", buffering=0)  # unbuffered ≈ live-safe
    print("opened new segment", path, flush=True)

def on_sample(sink):
    global current_fp, segment_start_ts_ns
    sample = sink.emit("pull-sample")
    if not sample:
        return Gst.FlowReturn.OK

    buf = sample.get_buffer()
    pts = buf.pts
    if pts == Gst.CLOCK_TIME_NONE:          # shouldn’t happen
        return Gst.FlowReturn.OK

    if (segment_start_ts_ns is None or
        pts - segment_start_ts_ns >= nanosec_per_seg):
        _rotate_segment(pts)

    ok, mapinfo = buf.map(Gst.MapFlags.READ)
    if ok and current_fp:
        current_fp.write(mapinfo.data)
        buf.unmap(mapinfo)

    return Gst.FlowReturn.OK

appsink.connect("new-sample", on_sample)

def _shutdown(*_):
    print("Shutting down…")
    pipeline.set_state(Gst.State.NULL)
    if current_fp:
        current_fp.close()
    loop.quit()

signal.signal(signal.SIGINT,  _shutdown)
signal.signal(signal.SIGTERM, _shutdown)

pipeline.set_state(Gst.State.PLAYING)
loop = GLib.MainLoop()
loop.run()
