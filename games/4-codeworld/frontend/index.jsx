import { React, Move, Box, Mix, Cobblestone, Air, render } from './WG.jsx';

function Scene({ size, mix }) {
    return <Move y={-60}>
        <Box sx={size} sy={size} sz={size} hollow>
            <Mix mix={mix} />
        </Box>
        <Move x={30}>
            <Box sx={size} sy={size} sz={size}>
                <Mix mix={mix} />
            </Box>
        </Move>
    </Move>;
}

// deno run --allow-net index.jsx
render(<Scene size={10} mix={{ 0.8: Cobblestone, 0.2: Air }} />);
