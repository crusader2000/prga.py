// Automatically generated by PRGA's RTL generator
{%- set cfg_width = module.ports.cfg_i|length %}
module fle6 (
    // user accessible ports
    input wire [0:0] clk,
    input wire [5:0] in,
    output reg [1:0] out,
    input wire [0:0] cin,
    output reg [0:0] cout,

    // configuartion ports
    input wire [0:0] cfg_clk,
    input wire [0:0] cfg_e,
    input wire [0:0] cfg_we,
    input wire [{{ cfg_width - 1 }}:0] cfg_i,
    output wire [{{ cfg_width - 1 }}:0] cfg_o
    );

    // 3 modes:
    //  1. LUT6 + optional DFF
    //  2. 2x (LUT5 + optional DFF)
    //  3. 2x LUT => adder => optional DFF for sum & cout_fabric
    
    localparam LUT5A_DATA_WIDTH = 32;
    localparam LUT5B_DATA_WIDTH = 32;
    localparam MODE_WIDTH = 2;

    localparam MODE_LUT6X1 = 2'd0;
    localparam MODE_LUT5X2 = 2'd1;
    localparam MODE_ARITH = 2'd3;

    localparam LUT5A_DATA = 0;
    localparam LUT5B_DATA = LUT5A_DATA + LUT5A_DATA_WIDTH;
    localparam ENABLE_FFA = LUT5B_DATA + LUT5B_DATA_WIDTH;
    localparam ENABLE_FFB = ENABLE_FFA + 1;
    localparam MODE = ENABLE_FFB + 1;
    localparam CIN_FABRIC = MODE + MODE_WIDTH;
    localparam CFG_BITCOUNT = CIN_FABRIC + 1;
    
    reg [CFG_BITCOUNT - 1:0] cfg_d;
    reg [5:0] internal_in;
    reg [1:0] internal_lut;
    reg [1:0] internal_ff;

    // synopsys translate_off
    // in case the sensitivity list is never triggered
    initial begin
        internal_in = 6'b0;
    end
    // synopsys translate_on

    always @* begin
        internal_in = in;

        // synopsys translate_off
        // in simulation, force unconnected LUT input to be zeros
        {%- for i in range(6) %}
        if (in[{{ i }}] === 1'bx) begin
            internal_in[{{ i }}] = 1'b0;
        end
        {%- endfor %}
        // synopsys translate_on
    end

    wire [1:0] internal_sum;
    assign internal_sum = internal_lut[0] + internal_lut[1] + (cfg_d[CIN_FABRIC] ? internal_in[5] : cin);

    wire [MODE_WIDTH-1:0] mode;
    assign mode = cfg_d[MODE +: MODE_WIDTH];

    always @(posedge clk) begin
        if (cfg_e) begin
            internal_ff <= 2'b0;
        end else if (mode == MODE_ARITH) begin
            internal_ff <= internal_sum;
        end else if (mode == MODE_LUT6X1) begin
            internal_ff[0] <= internal_in[5] ? internal_lut[1] : internal_lut[0];
            internal_ff[1] <= 1'b0;
        end else begin
            internal_ff <= internal_lut;
        end
    end

    always @* begin
        if (cfg_e) begin    // avoid pre-programming oscillating
            internal_lut = 2'b0;
        end else begin
            case (internal_in[4:0])     // synopsys infer_mux
                {%- for i in range(32) %}
                5'd{{ i }}: begin
                    internal_lut[0] = cfg_d[LUT5A_DATA + {{ i }}];
                    internal_lut[1] = cfg_d[LUT5B_DATA + {{ i }}];
                end
                {%- endfor %}
            endcase
        end
    end

    always @* begin
        if (cfg_e) begin    // avoid pre-programming oscillating
            out = 2'b0;
            cout = 1'b0;
        end else begin
            out = 2'b0;
            cout = 1'b0;

            case (mode)
                MODE_LUT6X1: begin
                    if (cfg_d[ENABLE_FFA]) begin
                        out[0] = internal_ff[0];
                    end else begin
                        out[0] = internal_in[5] ? internal_lut[1] : internal_lut[0];
                    end
                end
                MODE_LUT5X2: begin
                    if (cfg_d[ENABLE_FFA]) begin
                        out[0] = internal_ff[0];
                    end else begin
                        out[0] = internal_lut[0];
                    end
                    if (cfg_d[ENABLE_FFB]) begin
                        out[1] = internal_ff[1];
                    end else begin
                        out[1] = internal_lut[1];
                    end
                end
                MODE_ARITH: begin
                    if (cfg_d[ENABLE_FFA]) begin
                        out[0] = internal_ff[0];
                    end else begin
                        out[0] = internal_sum[0];
                    end
                    if (cfg_d[ENABLE_FFB]) begin
                        out[1] = internal_ff[1];
                    end else begin
                        out[1] = internal_sum[1];
                    end

                    cout = internal_sum[1];
                end
            endcase
        end
    end

    wire [CFG_BITCOUNT - 1 + {{ cfg_width }}:0] cfg_d_next;

    always @(posedge cfg_clk) begin
        if (cfg_e && cfg_we) begin
            cfg_d <= cfg_d_next;
        end
    end

    assign cfg_d_next = {{ '{' -}} cfg_d, cfg_i {{- '}' }};
    assign cfg_o = cfg_d_next[CFG_BITCOUNT +: {{ cfg_width }}];

endmodule
