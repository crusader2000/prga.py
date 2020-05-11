// Automatically generated by PRGA's RTL generator
//
// Adapter between a FIFO pull interface and a FIFO push interface
module prga_fifo_adapter #(
    parameter DATA_WIDTH = 32,
    parameter INPUT_LOOKAHEAD = 0
) (
    input wire [0:0] clk,
    input wire [0:0] rst,

    input wire [0:0] empty_i,
    output wire [0:0] rd_i,
    input wire [DATA_WIDTH - 1:0] dout_i,

    output wire [0:0] wr_o,
    input wire [0:0] full_o,
    output wire [DATA_WIDTH - 1:0] din_o
    );

    generate if (INPUT_LOOKAHEAD) begin
        assign rd_i = ~full_o;
        assign wr_o = ~empty_i;
        assign din_o = dout_i;
    end else begin
        wire empty_i_lookahead;
        assign wr_o = ~empty_i_lookahead;

        prga_fifo_lookahead_buffer #(
            .DATA_WIDTH             (DATA_WIDTH)
            ,.REVERSED              (0)
        ) buffer (
            .clk                    (clk)
            ,.rst                   (rst)
            ,.empty_i               (empty_i)
            ,.rd_i                  (rd_i)
            ,.dout_i                (dout_i)
            ,.empty                 (empty_i_lookahead)
            ,.rd                    (~full_o)
            ,.dout                  (din_o)
            );
    end endgenerate

endmodule