# Annotated disassembly of wpss.b07 (entry segment, RV32+RVC)
# file offset 16384 (vaddr 0x404000), first 250 instructions

00404000:  8962       c.lui      t0, 2                          
00404002:  93820280   addi       t0, t0, -0x800                 
00404006:  73a00230   csrs       mstatus, t0                    
0040400a:  73700430   csrci      mstatus, 8                     
0040400e:  97020000   auipc      t0, 0                          
00404012:  9382223f   addi       t0, t0, 0x3f2                  
00404016:  73905230   csrw       mtvec, t0                      
0040401a:  73e05130   csrsi      mtvec, 3                       
0040401e:  97610100   auipc      gp, 0x16                       
00404022:  9381a154   addi       gp, gp, 0x54a                  
00404026:  97220000   auipc      t0, 2                          
0040402a:  9382626c   addi       t0, t0, 0x6c6                  
0040402e:  03a30200   lw         t1, 0(t0)                      
00404032:  63040300   beqz       t1, 8                          
00404036:  6f20a062   j          0x262a                         
0040403a:  17510100   auipc      sp, 0x15                       
0040403e:  13016152   addi       sp, sp, 0x526                  
00404042:  1385419a   addi       a0, gp, -0x65c                 
00404046:  97e50100   auipc      a1, 0x1e                       
0040404a:  9385254e   addi       a1, a1, 0x4e2                  
0040404e:  ef40200a   jal        0x40a2                         
00404052:  13858186   addi       a0, gp, -0x798                 
00404056:  9385419a   addi       a1, gp, -0x65c                 
0040405a:  ef406009   jal        0x4096                         
0040405e:  6f00200a   j          0xa2                           
00404062:  0000       c.unimp                                   
00404064:  0000       c.unimp                                   
00404066:  0000       c.unimp                                   
00404068:  0000       c.unimp                                   
0040406a:  0000       c.unimp                                   
0040406c:  0000       c.unimp                                   
0040406e:  0000       c.unimp                                   
00404070:  0000       c.unimp                                   
00404072:  0000       c.unimp                                   
00404074:  0000       c.unimp                                   
00404076:  0000       c.unimp                                   
00404078:  0000       c.unimp                                   
0040407a:  0000       c.unimp                                   
0040407c:  0000       c.unimp                                   
0040407e:  0000       c.unimp                                   
00404080:  0000       c.unimp                                   
00404082:  0000       c.unimp                                   
00404084:  0000       c.unimp                                   
00404086:  0000       c.unimp                                   
00404088:  0000       c.unimp                                   
0040408a:  0000       c.unimp                                   
0040408c:  0000       c.unimp                                   
0040408e:  0000       c.unimp                                   
00404090:  0000       c.unimp                                   
00404092:  0000       c.unimp                                   
00404094:  0000       c.unimp                                   
00404096:  0000       c.unimp                                   
00404098:  0000       c.unimp                                   
0040409a:  0000       c.unimp                                   
0040409c:  0000       c.unimp                                   
0040409e:  0000       c.unimp                                   
004040a0:  0000       c.unimp                                   
004040a2:  0000       c.unimp                                   
004040a4:  0000       c.unimp                                   
004040a6:  0000       c.unimp                                   
004040a8:  0000       c.unimp                                   
004040aa:  0000       c.unimp                                   
004040ac:  0000       c.unimp                                   
004040ae:  0000       c.unimp                                   
004040b0:  0000       c.unimp                                   
004040b2:  0000       c.unimp                                   
004040b4:  0000       c.unimp                                   
004040b6:  0000       c.unimp                                   
004040b8:  0000       c.unimp                                   
004040ba:  0000       c.unimp                                   
004040bc:  0000       c.unimp                                   
004040be:  0000       c.unimp                                   
004040c0:  0000       c.unimp                                   
004040c2:  0000       c.unimp                                   
004040c4:  0000       c.unimp                                   
004040c6:  0000       c.unimp                                   
004040c8:  0000       c.unimp                                   
004040ca:  0000       c.unimp                                   
004040cc:  0000       c.unimp                                   
004040ce:  0000       c.unimp                                   
004040d0:  0000       c.unimp                                   
004040d2:  0000       c.unimp                                   
004040d4:  0000       c.unimp                                   
004040d6:  0000       c.unimp                                   
004040d8:  0000       c.unimp                                   
004040da:  0000       c.unimp                                   
004040dc:  0000       c.unimp                                   
004040de:  0000       c.unimp                                   
004040e0:  0000       c.unimp                                   
004040e2:  0000       c.unimp                                   
004040e4:  0000       c.unimp                                   
004040e6:  0000       c.unimp                                   
004040e8:  0000       c.unimp                                   
004040ea:  0000       c.unimp                                   
004040ec:  0000       c.unimp                                   
004040ee:  0000       c.unimp                                   
004040f0:  0000       c.unimp                                   
004040f2:  0000       c.unimp                                   
004040f4:  0000       c.unimp                                   
004040f6:  0000       c.unimp                                   
004040f8:  0000       c.unimp                                   
004040fa:  0000       c.unimp                                   
004040fc:  0000       c.unimp                                   
004040fe:  0000       c.unimp                                   
00404100:  97420100   auipc      t0, 0x14                       
00404104:  93820200   mv         t0, t0                         
00404108:  03a30200   lw         t1, 0(t0)                      
0040410c:  630c0300   beqz       t1, 0x18                       
00404110:  97430100   auipc      t2, 0x14                       
00404114:  938343ff   addi       t2, t2, -0xc                   
00404118:  03a30300   lw         t1, 0(t2)                      
0040411c:  93021300   addi       t0, t1, 1                      
00404120:  23a05300   sw         t0, 0(t2)                      
00404124:  6f20b012   j          0x292a                         
00404128:  0000       c.unimp                                   
0040412a:  0000       c.unimp                                   
0040412c:  0000       c.unimp                                   
0040412e:  0000       c.unimp                                   
00404130:  0000       c.unimp                                   
00404132:  0000       c.unimp                                   
00404134:  0000       c.unimp                                   
00404136:  0000       c.unimp                                   
00404138:  0000       c.unimp                                   
0040413a:  0000       c.unimp                                   
0040413c:  0000       c.unimp                                   
0040413e:  0000       c.unimp                                   
00404140:  0000       c.unimp                                   
00404142:  0000       c.unimp                                   
00404144:  0000       c.unimp                                   
00404146:  0000       c.unimp                                   
00404148:  0000       c.unimp                                   
0040414a:  0000       c.unimp                                   
0040414c:  0000       c.unimp                                   
0040414e:  0000       c.unimp                                   
00404150:  0000       c.unimp                                   
00404152:  0000       c.unimp                                   
00404154:  0000       c.unimp                                   
00404156:  0000       c.unimp                                   
00404158:  0000       c.unimp                                   
0040415a:  0000       c.unimp                                   
0040415c:  0000       c.unimp                                   
0040415e:  0000       c.unimp                                   
00404160:  0000       c.unimp                                   
00404162:  0000       c.unimp                                   
00404164:  0000       c.unimp                                   
00404166:  0000       c.unimp                                   
00404168:  0000       c.unimp                                   
0040416a:  0000       c.unimp                                   
0040416c:  0000       c.unimp                                   
0040416e:  0000       c.unimp                                   
00404170:  0000       c.unimp                                   
00404172:  0000       c.unimp                                   
00404174:  0000       c.unimp                                   
00404176:  0000       c.unimp                                   
00404178:  0000       c.unimp                                   
0040417a:  0000       c.unimp                                   
0040417c:  0000       c.unimp                                   
0040417e:  0000       c.unimp                                   
00404180:  0000       c.unimp                                   
00404182:  0000       c.unimp                                   
00404184:  0000       c.unimp                                   
00404186:  0000       c.unimp                                   
00404188:  0000       c.unimp                                   
0040418a:  0000       c.unimp                                   
0040418c:  0000       c.unimp                                   
0040418e:  0000       c.unimp                                   
00404190:  0000       c.unimp                                   
00404192:  0000       c.unimp                                   
00404194:  0000       c.unimp                                   
00404196:  0000       c.unimp                                   
00404198:  0000       c.unimp                                   
0040419a:  0000       c.unimp                                   
0040419c:  0000       c.unimp                                   
0040419e:  0000       c.unimp                                   
004041a0:  0000       c.unimp                                   
004041a2:  0000       c.unimp                                   
004041a4:  0000       c.unimp                                   
004041a6:  0000       c.unimp                                   
004041a8:  0000       c.unimp                                   
004041aa:  0000       c.unimp                                   
004041ac:  0000       c.unimp                                   
004041ae:  0000       c.unimp                                   
004041b0:  0000       c.unimp                                   
004041b2:  0000       c.unimp                                   
004041b4:  0000       c.unimp                                   
004041b6:  0000       c.unimp                                   
004041b8:  0000       c.unimp                                   
004041ba:  0000       c.unimp                                   
004041bc:  0000       c.unimp                                   
004041be:  0000       c.unimp                                   
004041c0:  0000       c.unimp                                   
004041c2:  0000       c.unimp                                   
004041c4:  0000       c.unimp                                   
004041c6:  0000       c.unimp                                   
004041c8:  0000       c.unimp                                   
004041ca:  0000       c.unimp                                   
004041cc:  0000       c.unimp                                   
004041ce:  0000       c.unimp                                   
004041d0:  0000       c.unimp                                   
004041d2:  0000       c.unimp                                   
004041d4:  0000       c.unimp                                   
004041d6:  0000       c.unimp                                   
004041d8:  0000       c.unimp                                   
004041da:  0000       c.unimp                                   
004041dc:  0000       c.unimp                                   
004041de:  0000       c.unimp                                   
004041e0:  0000       c.unimp                                   
004041e2:  0000       c.unimp                                   
004041e4:  0000       c.unimp                                   
004041e6:  0000       c.unimp                                   
004041e8:  0000       c.unimp                                   
004041ea:  0000       c.unimp                                   
004041ec:  0000       c.unimp                                   
004041ee:  0000       c.unimp                                   
004041f0:  0000       c.unimp                                   
004041f2:  0000       c.unimp                                   
004041f4:  0000       c.unimp                                   
004041f6:  0000       c.unimp                                   
004041f8:  0000       c.unimp                                   
004041fa:  0000       c.unimp                                   
004041fc:  0000       c.unimp                                   
004041fe:  0000       c.unimp                                   
00404200:  3971       c.addi16sp sp, -0x40                      
00404202:  06c0       c.swsp     ra, 0(sp)                      
00404204:  16c2       c.swsp     t0, 4(sp)                      
00404206:  1ac4       c.swsp     t1, 8(sp)                      
00404208:  1ec6       c.swsp     t2, 0xc(sp)                    
0040420a:  2ac8       c.swsp     a0, 0x10(sp)                   
0040420c:  2eca       c.swsp     a1, 0x14(sp)                   
0040420e:  32cc       c.swsp     a2, 0x18(sp)                   
00404210:  36ce       c.swsp     a3, 0x1c(sp)                   
00404212:  3ad0       c.swsp     a4, 0x20(sp)                   
00404214:  3ed2       c.swsp     a5, 0x24(sp)                   
00404216:  42d4       c.swsp     a6, 0x28(sp)                   
00404218:  46d6       c.swsp     a7, 0x2c(sp)                   
0040421a:  72d8       c.swsp     t3, 0x30(sp)                   
0040421c:  76da       c.swsp     t4, 0x34(sp)                   
0040421e:  7adc       c.swsp     t5, 0x38(sp)                   
00404220:  7ede       c.swsp     t6, 0x3c(sp)                   
00404222:  b122       c.jal      0x14c                          
00404224:  8962       c.lui      t0, 2                          
00404226:  93820280   addi       t0, t0, -0x800                 
0040422a:  73a00230   csrs       mstatus, t0                    
0040422e:  8240       c.lwsp     ra, 0(sp)                      
00404230:  9242       c.lwsp     t0, 4(sp)                      
00404232:  2243       c.lwsp     t1, 8(sp)                      
00404234:  b243       c.lwsp     t2, 0xc(sp)                    
00404236:  4245       c.lwsp     a0, 0x10(sp)                   
00404238:  d245       c.lwsp     a1, 0x14(sp)                   
0040423a:  6246       c.lwsp     a2, 0x18(sp)                   

# total decoded: 250
