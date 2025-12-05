MODULE Project_40
    !Posiciones virtuales PCAM (Posición para la cámara), SP (Posición de seguridad) y EX (Posición en la que el robot se deshace de la pieza)
    CONST robtarget PCAM := [[450,0,300],[0,0,1,0],[0,0,0,0],[9E+09,9E+09,9E+09,9E+09,9E+09,9E+09]];
    CONST robtarget SP := [[591.08,-190.88,277.06],[0.28363,0.75801,0.55172,0.20147],[0,0,0,0],[9E+09,9E+09,9E+09,9E+09,9E+09,9E+09]];
    CONST robtarget EX := [[591.08,-190.88,277.06],[0.34783,0.29059,0.89138,-0.00309],[0,0,0,0],[9E+09,9E+09,9E+09,9E+09,9E+09,9E+09]];
    
    !Posiciones virtuales P1, P2, P3, P4 Y RSP (Posición para row_sweep)
    VAR robtarget matriz_P1{3,3,4};
    VAR robtarget matriz_P2{3,3,4};
    VAR robtarget matriz_P3{3,3,4};
    VAR robtarget matriz_P4{3,3,4};
    VAR robtarget P1;
    VAR robtarget P2;
    VAR robtarget P3;
    VAR robtarget P4;
    VAR robtarget RSP;
    
    VAR num i;
    VAR num j;
    VAR num k;
    
    VAR num row;
    VAR num col;
    VAR num height;
    
    VAR socketdev server;
    VAR socketdev client;
    VAR rawbytes sent_data;
    
    !Distancia entre columnas y filas respectivamente
    CONST num offset_x{3,3} := [[0,148,303],[0,148,303],[0,148,303]];
    CONST num offset_z{3,3} := [[0,3.97,5.32],[115.5,122.4,123.46],[230.22,236.37,235.02]];
    
    CONST num forward := 120;
    CONST num lift := 17;
    
    !Posición inicial virtual (matriz_P1{1,1,1})
    CONST num x0 := 189.53;
    CONST num y0 := -406.83;
    CONST num z0 := 450.93;
    CONST num q1 := 0.33198;
    CONST num q2 := 0.94271;
    CONST num q3 := -0.03167;
    CONST num q4 := -0.00931;
    
   PROC main()
        ! Inicialización
        row_sweep;
        WaitTime 1;
        calc_pos;
        
        ! Mover a posición segura
        MoveJ SP, v1000, z50, pinza\WObj:=table;
        
        TPWrite "Sistema iniciado. Esperando conexiones...";
        
        ! Main communication loop
        WHILE TRUE DO
            ! Open socket server
            SocketCreate server;
            SocketBind server, "192.168.125.1", 9119;
            SocketListen server;
            
            TPWrite "Esperando conexion...";
            
            ! Accept client connection
            SocketAccept server, client;
            TPWrite "Cliente conectado!";
            
            ! Receive data (12 bytes = 3 integers of 4 bytes each)
            SocketReceive client, \RawData:=sent_data, \ReadNoOfBytes:=12;
            
            ! Unpack received data
            UnpackRawBytes sent_data, 1, row, \IntX:=DINT;
            UnpackRawBytes sent_data, 5, col, \IntX:=DINT;
            UnpackRawBytes sent_data, 9, height, \IntX:=DINT;
            
            ! **CONVERTIR DE ÍNDICES PYTHON (0-2) A RAPID (1-3)**
            row := row + 1;
            col := col + 1;
            
            ! **CORREGIDO: Usar row y col en lugar de i y j**
            TPWrite "Recibido: Fila=" + NumToStr(row,0) + " Col=" + NumToStr(col,0);
            
            ! Execute pick and place
            execute;
            
            ! Send confirmation
            SocketSend client, \Str:="OK";
            TPWrite "Tarea completada!";
            
            ! Close sockets
            SocketClose client;
            SocketClose server;
            
            ! Return to safe position
            MoveJ SP, v1000, z50, pinza\WObj:=table;
        ENDWHILE
        execute;
    ENDPROC
    
    PROC row_sweep()     
        MoveJ SP,v150,z1,pinza\WObj:=table;
        !Calculamos posición RSP para 3 columnas
        FOR j FROM 1 TO 3 DO
            RSP := [[x0-offset_x{1,j},y0,z0-offset_z{1,j}],[q1,q2,q3,q4],[0,0,0,0],[9E+09,9E+09,9E+09,9E+09,9E+09,9E+09]];
            MoveL RSP,v100,z1,pinza\WObj:=table;
            WaitTime 1;
        ENDFOR
        MoveL SP,v100,z1,pinza\WObj:=table;
    ENDPROC
    
    PROC calc_pos()
        !Calculamos las posiciones virtuales P1, P2, P3 Y P4 para cada bloque de la estantería
        FOR i FROM 1 TO 3 DO
            FOR j FROM 1 TO 3 DO
                !matriz_P1{i,j,1} := [[x0-(j-1)*Dx,y0,z0-(i-1)*Dz], [q1,q2,q3,q4], [0,0,1,0], [9E+09,9E+09,9E+09,9E+09,9E+09,9E+09]];
                !matriz_P2{i,j,1} := [[x0-(j-1)*Dx,-776.28, z0-(i-1)*Dz], [q1,q2,q3,q4], [0,0,1,0], [9E+09,9E+09,9E+09,9E+09,9E+09,9E+09]];
                !matriz_P3{i,j,1} := [[47.76-(j-1)*Dx,-776.28,339.75-(i-1)*Dz], [q1,q2,q3,q4], [0,0,1,0], [9E+09,9E+09,9E+09,9E+09,9E+09,9E+09]];
                !matriz_P4{i,j,1} := [[47.76-(j-1)*Dx,y0,339.75-(i-1)*Dz], [q1,q2,q3,q4], [0,0,1,0], [9E+09,9E+09,9E+09,9E+09,9E+09,9E+09]];
                matriz_P1{i,j,1} := [[x0-offset_x{i,j},y0,z0-offset_z{i,j}], [q1,q2,q3,q4], [0,0,1,0], [9E+09,9E+09,9E+09,9E+09,9E+09,9E+09]];
                matriz_P2{i,j,1} := matriz_P1{i,j,1};
                matriz_P2{i,j,1}.trans.y := matriz_P1{i,j,1}.trans.y-forward;
                matriz_P3{i,j,1} := matriz_P2{i,j,1};
                matriz_P3{i,j,1}.trans.z := matriz_P2{i,j,1}.trans.z+lift;
                matriz_P4{i,j,1} := matriz_P3{i,j,1};
                matriz_P4{i,j,1}.trans.y := matriz_P2{i,j,1}.trans.y+forward;
            ENDFOR
        ENDFOR
    ENDPROC
    
    PROC execute()
        !Posición inventada para la simulación (fila = 2, columna = 2)
        P1 := matriz_P1{row,col,1};
        P2 := matriz_P2{row,col,1};
        P3 := matriz_P3{row,col,1};
        P4 := matriz_P4{row,col,1};        
        MoveL P1,v100,z1,pinza\WObj:=table;
        WaitTime 0.5;
        MoveL P2,v20,z1,pinza\WObj:=table;
        WaitTime 0.5;
        MoveL P3,v20,z1,pinza\WObj:=table;
        WaitTime 0.5;
        MoveL P4,v20,z1,pinza\WObj:=table;
        WaitTime 0.5;
!        P1 := matriz_P1{2,1,1};
!        P2 := matriz_P2{2,1,1};
!        P3 := matriz_P3{2,1,1};
!        P4 := matriz_P4{2,1,1};
!        MoveJ P4,v100,z1,pinza\WObj:=table;
!        WaitTime 0.5;
!        MoveL P3,v20,z1,pinza\WObj:=table;
!        WaitTime 0.5;
!        MoveL P2,v20,z1,pinza\WObj:=table;
!        WaitTime 0.5;
!        MoveL P1,v20,z1,pinza\WObj:=table;
!        WaitTime 0.5;
        MoveL SP,v100,z1,pinza\WObj:=table;
        MoveJ EX,v100,z1,pinza\WObj:=table;
        WaitTime 2;
        MoveJ SP,v100,z1,pinza\WObj:=table;
    ENDPROC
ENDMODULE
