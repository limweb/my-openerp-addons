<html>
<head>

<script>
function insert_demo_top(id)
{

	if (window.XMLHttpRequest) {// code for IE7+, Firefox, Chrome, Opera, Safari
  		xmlhttp=new XMLHttpRequest();
  	} else {// code for IE6, IE5
  		xmlhttp=new ActiveXObject("Microsoft.XMLHTTP");
  	}
	xmlhttp.onreadystatechange=function() {
  		if (xmlhttp.readyState==4 && xmlhttp.status==200) {
    			document.getElementById("txtHint").innerHTML=xmlhttp.responseText;
    		}
  	}
	xmlhttp.open("GET","insert_demo_top.php?id="+id,true);
	xmlhttp.send();
	window.alert("Save Complete")

}
function insert_demo_bigc(id)
{

	if (window.XMLHttpRequest) {// code for IE7+, Firefox, Chrome, Opera, Safari
  		xmlhttp=new XMLHttpRequest();
  	} else {// code for IE6, IE5
  		xmlhttp=new ActiveXObject("Microsoft.XMLHTTP");
  	}
	xmlhttp.onreadystatechange=function() {
  		if (xmlhttp.readyState==4 && xmlhttp.status==200) {
    			document.getElementById("txtHint").innerHTML=xmlhttp.responseText;
    		}
  	}
	xmlhttp.open("GET","insert_demo_big-c.php?id="+id,true);
	xmlhttp.send();
	window.alert("Save Complete")

}
</script>
	
</head>

<?php
	session_start();
	$_SESSION['uid'] = $_GET['uid'];
	$_SESSION['pwd'] = $_GET['pwd'];
	$_SESSION['dbname'] = $_GET['dbname'];
	$_SESSION['host'] = $_GET['host'];
?>
<body>
  	<table width="100%">
    	<tr>
			<td height="400px">
				<table width="100%">
					<tr>
						<td>Period Select: 
							<select>
  								<option value="wk20">Week21</option>
  								<option value="wk21">Week22</option>
							</select>	
						</td>
					</tr>
					<tr>
						<td>
								<table width="100%" border="1">
									<tr>
										<td>TOPS</td>
										<td>
											<input type="checkbox" name="vehicle" value="top-a" /> Group A (5/20)
											<br />
											<input type="checkbox" name="vehicle" value="top-b" /> Group B (0/20)
											<br />
											<input type="checkbox" name="vehicle" value="top-c" /> Group C (0/15)</td>
									</tr>
									<tr>
										<td>BIG-C</td>
										<td>
											<input type="checkbox" name="vehicle" value="big-a" /> Group A (0/25)
											<br />
											<input type="checkbox" name="vehicle" value="big-b" /> Group B (4/20)
											<br />
											<input type="checkbox" name="vehicle" value="big-c" /> Group C (7/15)</td>
										</td>
									</tr>
								<table>
						</td>
					</tr>
				</table>
			</td>
		</tr>
    	<tr>
			<td>
				<form name='myForm'>	
				<?php echo "<input type='button' onclick='insert_demo_top(".$_GET['id'] .")' value='Demo Insert Tops' />" ?>	
				<?php echo "<input type='button' onclick='insert_demo_bigc(".$_GET['id'] .")' value='Demo Insert Big-C' />" ?>	
				</form>
			</td>
		</tr>
  </table>
</body>
</html>
