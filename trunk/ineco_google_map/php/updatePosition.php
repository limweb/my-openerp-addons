<?php
     	include("xmlrpc.inc");

	$id = $_GET['id'];
	$lng = $_GET['lng'];
	$lat = $_GET['lat'];	

	session_start(); 
     	$user = $_SESSION['uid'];
     	$password = $_SESSION['pwd'];
     	$dbname = $_SESSION['dbname'];
     	$server_url = 'http://'.$_SESSION['host'].':8069/xmlrpc/';

     	$id_val = array();
     	$id_val[0] = new xmlrpcval($id, "int");

	$sock = new xmlrpc_client($server_url.'common');
	$msg = new xmlrpcmsg('login');
	$msg->addParam(new xmlrpcval($dbname, "string"));
	$msg->addParam(new xmlrpcval($user, "string"));
	$msg->addParam(new xmlrpcval($password, "string"));
   	$resp =  $sock->send($msg);
   	$val = $resp->value();
   	$user_id = $val->scalarval();
		
	$data = array(
		'latitude' =>new xmlrpcval($lat, "string") ,
		'longtitude' =>new xmlrpcval($lng , "string")
	);

	$client = new xmlrpc_client("http://".$_SESSION['host'].":8069/xmlrpc/object");

     	$msg = new xmlrpcmsg('execute');
     	$msg->addParam(new xmlrpcval($dbname, "string"));
     	$msg->addParam(new xmlrpcval($user_id, "int"));
     	$msg->addParam(new xmlrpcval($password, "string"));
     	$msg->addParam(new xmlrpcval("res.partner.address", "string"));
     	$msg->addParam(new xmlrpcval("write", "string"));
     	$msg->addParam(new xmlrpcval($id_val, "array"));
     	$msg->addParam(new xmlrpcval($data, "struct"));

     	$resp = $client->send($msg);
     	$val = $resp->value();
     	$record = $val->scalarval();
	
?>
