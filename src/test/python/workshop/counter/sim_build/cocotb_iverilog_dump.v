module cocotb_iverilog_dump();
initial begin
    $dumpfile("sim_build/Counter.fst");
    $dumpvars(0, Counter);
end
endmodule
