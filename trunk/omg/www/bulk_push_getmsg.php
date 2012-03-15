<?
//Get Global parameter from HTTP Header
if (!empty($_GET)) {
    extract($_GET);
} else if (!empty($HTTP_GET_VARS)) {
    extract($HTTP_GET_VARS);
} // end if
if (!empty($_POST)) {
    extract($_POST);
} else if (!empty($HTTP_POST_VARS)) {
    extract($HTTP_POST_VARS);
} // end if

$ctype="TEXT";
$ip_client="127.0.0.1";
$data ="TRANSID=BULK&CMD=SENDMSG&FROM=9009000&TO=".$msisdn."&REPORT=Y&CHARGE=Y&CODE=TEXT&CTYPE=$ctype&CONTENT=".$message;
$len = strlen($data);
header("Content-Type: text/xml");
$fp = fsockopen ($ip_client, 81, $errno, $errstr, 30);
		if (!$fp) {
			$status="Connection failed";
		} else {
			fputs ($fp, "POST / HTTP/1.1\r\nContent-type:application/x-www-form-urlencoded\r\nContent-length: $len\r\n\r\n$data");
			$xml=""; 
			while (!feof($fp)) { $xml= $xml.fgets($fp,128);}
			fclose ($fp);
		}
		
$xml=strstr($xml,"<XML>");
echo $xml;
?>