��    �      ,  �   <      �
    �
  9     
   A     L     Y     [  �  ]               !     /     6     L  	   U  a   _     �     �     �     �                               &     @     E     K     T     ]     d     m     �     �     �     �     �     �     �     �  &   �  (         I     Q     V     [     `     t     z     ~     �     �     �     �     �     �     �     �     �       Q     !   d     �     �  
   �  
   �  +   �                    '     4     <     H  
   [     f     {     �  +   �     �     �     �     �     �                 	   -  	   7     A     H  
   N     Y     i     ~     �     �     �  
   �  A   �  d   �  '   X  E   �  9  �                       \   +  O   �     �  )   �            
   0     ;     O     a     m  P  �  
   �     �     �  >   �  >   0  1   o  :   �     �     �  �      �  �   �"     8#     K#     ^#     `#  �  b#     %     ,%     B%     P%  6   c%     �%     �%  a   �%     "&     1&  -   >&     l&     �&     �&  	   �&     �&     �&  <   �&     #'     ?'     L'  '   e'     �'     �'  ?   �'     (     (  *   .(     Y(     v(     �(  *   �(     �(  K   �(  Z   1)     �)     �)     �)  	   �)     �)  !   �)     *     /*     ?*     H*     W*     s*  6   �*  0   �*  ?   �*  '   .+  6   V+  ?   �+  Q   �+  !   ,  3   A,     u,  $   �,     �,  �   �,  $   [-  !   �-  -   �-  $   �-     �-  !   .  6   3.     j.     �.  E   �.     �.  +   �.  $   &/     K/  *   [/     �/     �/  *   �/     �/  *   �/     �/  	   0     0     +0  *   ;0  3   f0  *   �0  %   �0  !   �0     1     1  
   -1  �   81  d   �1  j   12  E   �2  9  �2     4     54     T4  '   m4  \   �4  O   �4     B5  )   N5     x5     �5     �5  9   �5  -   �5     6  -   :6  P  h6  
   �7     �7     �7  �   �7  >   �8  V   �8  �   9     �9     �9        A   [   C   k   Y   q   :      7       ;   �   m   f   v           5   p   j   	             K               &   y       t               F       =             /       g           s   9   J      u   z   3   6       D   ?   Q   e   \   G       a   -      c   P      L      �      b   !              @      0               )   }       N   <   |       l          *      d   #       %   (   T   �   ~      2   1   n                  w                     +      '       E       I           S   O   H   x   ]   U   
   ,   $                     h            M   V      `             X   "   _   4   i       o   B   R   .   {   Z   ^   >          8   r   W        
     This module adds state, date_start,date_stop in production order operation lines
     (in the "Work Centers" tab)
     State: draft, confirm, done, cancel
     When finishing/confirming,cancelling production orders set all state lines to the according state
     Create menus:
         Production Management > All Operations
         Production Management > All Operations > Operations To Do (state="confirm")
     Which is a view on "Work Centers" lines in production order,
     editable tree

    Add buttons in the form view of production order under workcenter tab:
    * start (set state to confirm), set date_start
    * done (set state to done), set date_stop
    * set to draft (set state to draft)
    * cancel set state to cancel

    When the production order becomes "ready to produce", operations must
    become 'confirmed'. When the production order is done, all operations
    must become done.

    The field delay is the delay(stop date - start date).
    So that we can compare the theoretic delay and real delay.

      You cannot Resume the operation other then Pause state ! # of Lines #Line Orders ( ) * When a work order is created it is set in 'Draft' state.
* When user sets work order in start mode that time it will be set in 'In Progress' state.
* When work order is in running mode, during that time if user wants to stop or to make changes in order then can set in 'Pause' state.
* When the user cancels the work order it will be set in 'Canceled' state.
* When order is completely processed that time it is set in 'Finished' state. April August Calendar View Cancel Cancel the operation. Canceled Cancelled Check this to be able to move independently all production orders, without moving dependent ones. Children Moves Code Confirmed Work Orders Creation of the work order Current Date Day December Delay Details of the work order Done Draft Duration End Date Error! February Finish the operation. Finished Free Serialisation Future Work Orders Group By... Hours by Work Center In Production In Progress Information Information from the production order. Information from the routing definition. January July June Late Manufacturing Order March May Month Month -1 Mrp Operations November October Operation Cancelled Operation Codes Operation Done Operation Name Operation cancelled Operation done Operation has already started !You  can either Pause /Finish/Cancel the operation Operation is Already Cancelled  ! Operation is already finished ! Operation is not started yet ! Operations Order Date Order quantity cannot be negative or zero ! Pause Pending Picking Exception Planned Date Product Product Qty Product to Produce Production Production Operation Production Operation Code Production Order Production Order Cannot start in [%s] state Production State Qty Ready to Produce Real Resume Scheduled Date Search Search Work Orders September Set Draft Sorry! Start Start Date Start Operation Start the operation. Start/Stop Barcode Started State Status Stock Move The work orders are created on the basis of the production order. There is 1 work order per work center. The information about the number of cycles or the cycle time. There is no Operation to be cancelled ! This is lead time between operation start and stop in this workcenter To manufacture or assemble products, and use raw materials and finished products you must also handle manufacturing operations. Manufacturing operations are often called Work Orders. The various operations will have different impacts on the costs of manufacturing and planning depending on the available workload. Total Cycles Total Hours UOM Waiting Goods When the operation is finished, the operator updates the system by finishing the work order. When the operation needs to be cancelled, you can do it in the work order form. Work Center Work Center Production start end workflow Work Centers Work Centers Barcode Work Order Work Order Analysis Work Order Report Work Orders Work Orders Planning Work Orders is the list of operations to be performed for each manufacturing order. Once you start the first work order of a manufacturing order, the manufacturing order is automatically marked as started. Once you finish the latest operation of a manufacturing order, the MO is automatically done and the related products are produced. Workcenter Working Hours Year You cannot Pause the Operation other then Start/Resume state ! You cannot finish the operation without Starting/Resuming it ! You must assign a production lot for this product You try to assign a lot which is not from the same product mrp_operations.operation mrp_operations.operation.code Project-Id-Version: OpenERP Server 6.0dev_rc3
Report-Msgid-Bugs-To: support@openerp.com
POT-Creation-Date: 2011-01-03 16:58+0000
PO-Revision-Date: 2011-06-25 11:37+0700
Last-Translator: Tititab Srisookco
Language-Team: 
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 8bit
X-Launchpad-Export-Date: 2011-01-06 05:21+0000
X-Generator: Launchpad (build Unknown)
 
     This module adds state, date_start,date_stop in production order operation lines
     (in the "Work Centers" tab)
     State: draft, confirm, done, cancel
     When finishing/confirming,cancelling production orders set all state lines to the according state
     Create menus:
         Production Management > All Operations
         Production Management > All Operations > Operations To Do (state="confirm")
     Which is a view on "Work Centers" lines in production order,
     editable tree

    Add buttons in the form view of production order under workcenter tab:
    * start (set state to confirm), set date_start
    * done (set state to done), set date_stop
    * set to draft (set state to draft)
    * cancel set state to cancel

    When the production order becomes "ready to produce", operations must
    become 'confirmed'. When the production order is done, all operations
    must become done.

    The field delay is the delay(stop date - start date).
    So that we can compare the theoretic delay and real delay.

     คุณไม่สามารถเริ่มดำเนินการอื่น ๆ แล้วรัฐหยุด! รายการ รายการ ( ) * When a work order is created it is set in 'Draft' state.
* When user sets work order in start mode that time it will be set in 'In Progress' state.
* When work order is in running mode, during that time if user wants to stop or to make changes in order then can set in 'Pause' state.
* When the user cancels the work order it will be set in 'Canceled' state.
* When order is completely processed that time it is set in 'Finished' state. เมษายน สิงหาคม Calendar View ยกเลิก ยกเลิกการดำเนินการ ยกเลิก ยกเลิก Check this to be able to move independently all production orders, without moving dependent ones. Children Moves รหัส ยืนยันใบสั่งงาน Creation of the work order ปัจจุบัน วันที่ วัน ธันวาคม ล่าช้า รายละเอียดการสั่งงาน เสร็จสิ้น ร่าง ระยะเวลา วันที่สิ้นสุด ข้อผิดพลาด กุมภาพันธ์ การดำเนินการเสร็จสิ้น เสร็จ Free Serialisation ใบสั่งงานอนาคต กลุ่มตาม ... Hours by Work Center กำลังผลิต กำลังดำเนินการ ข้อมูล ข้อมูลที่ได้จากคำสั่งผลิต ข้อมูลที่ได้จากการกำหนดเส้นทาง มกราคม กรกฎาคม มิถุนายน ช้า ใบสั่งผลิต เดือนมีนาคม พฤษภาคม เดือน Month -1 Mrp Operations พฤศจิกายน ตุลาคม ยกเลิกการดำเนินงาน รหัสการดำเนินงาน การดำเนินงานเสร็จสิ้น ชื่อกระบวนการ การดำเนินถูกยกเลิก การดำเนินการเสร็จสิ้น Operation has already started !You  can either Pause /Finish/Cancel the operation Operation is Already Cancelled  ! การทำงานเสร็จสิ้น Operation is not started yet ! การดำเนินงาน วันที่สั่ง ปริมาณการสั่งซื้อไม่สามารถติดลบหรือศูนย์ได้! หยุดชั่วคราว รอดำเนินการ ใบจัดของผิดพลาด วันที่ตามแผน ผลิตภัณฑ์ จำนวนสินค้า ผลิตภัณฑ์ที่จะผลิต การผลิต Production Operation รหัสการดำเนินงานการผลิต ใบสั่งผลิต Production Order Cannot start in [%s] state สถานะการผลิต จำนวน พร้อมที่จะผลิต จริง Resume กำหนดการวันที่ Search ค้นหาใบสั่งงาน กันยายน Set Draft ขออภัย! เริ่ม วันที่เริ่มต้น ดำเนินการเริ่มต้น เริ่มดำเนินการ Start / Stop บาร์โค้ด การเริ่มต้น สถานะ สถานะ Stock Move คำสั่งงานจะถูกสร้างขึ้นบนพื้นฐานของการสั่งการผลิต There is 1 work order per work center. The information about the number of cycles or the cycle time. มีการดำเนินงานให้มีการยกเลิกไม่เป็น! This is lead time between operation start and stop in this workcenter To manufacture or assemble products, and use raw materials and finished products you must also handle manufacturing operations. Manufacturing operations are often called Work Orders. The various operations will have different impacts on the costs of manufacturing and planning depending on the available workload. จำนวนรอบ ชั่วโมงรวม หน่วยนับ กำลังรอสินค้า When the operation is finished, the operator updates the system by finishing the work order. When the operation needs to be cancelled, you can do it in the work order form. Work Center Work Center Production start end workflow Work Centers Work Centers Barcode ใบสั่งงาน การวิเคราะห์สั่งงาน รายงานใบสั่งงาน ใบสั่งงาน วางแผนใบสั่งงาน Work Orders is the list of operations to be performed for each manufacturing order. Once you start the first work order of a manufacturing order, the manufacturing order is automatically marked as started. Once you finish the latest operation of a manufacturing order, the MO is automatically done and the related products are produced. Workcenter เวลาทำการ ปี คุณไม่สามารถหยุดการดำเนินงานอื่น ๆ จากสถานะ เริ่มต้น / Resume ! You cannot finish the operation without Starting/Resuming it ! คุณต้องกำหนด LOT สำหรับสินค้านี้ คุณพยายามที่จะกำหนดจำนวนมากที่ไม่ได้จากผลิตภัณฑ์เดียวกัน mrp_operations.operation mrp_operations.operation.code 