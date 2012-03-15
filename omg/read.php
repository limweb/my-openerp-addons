<?php
	include("xmlrpc.inc");

	$user = "admin";
	$password = "admin";
	$db = "newomg";
	$serverUri = "http://localhost:8069/xmlrpc/";
	
	$client = new xmlrpc_client($serverUri.'common');
	
	$msg = new xmlrpcmsg('login');
	$msg->addParam(new xmlrpcval($db, "string"));
	$msg->addParam(new xmlrpcval($user, "string"));
	$msg->addParam(new xmlrpcval($password, "string"));


	$res =  &$client->send($msg);

	if(!$res->faultCode()){
		$id = $res->value()->scalarval();	

		$client = new xmlrpc_client($serverUri.'object');

		$key = array(new xmlrpcval(array(new xmlrpcval("id", "string"),
					new xmlrpcval("<>", "string"),
					new xmlrpcval(-1, "int")),"array"),);
					
		
				
		$msg = new xmlrpcmsg('execute');
		$msg->addParam(new xmlrpcval($db, "string"));
		$msg->addParam(new xmlrpcval($id, "int"));
		$msg->addParam(new xmlrpcval($password, "string"));
		$msg->addParam(new xmlrpcval("omg.sale.chain","string"));
		$msg->addParam(new xmlrpcval("search", "string"));		
		$msg->addParam(new xmlrpcval($key, "array"));
		$msg->addParam(new xmlrpcval(0, "int"));
		$msg->addParam(new xmlrpcval(0, "int"));
		$msg->addParam(new xmlrpcval("name ASC", "string"));
		
		$res = &$client->send($msg);

		if(!$res->faultCode())
		{
			$val = $res->value()->scalarval();
			
			$ides = array();
			
			for ($i=0 ; $i<count($val); $i++)
			{
				array_push($ides, new xmlrpcval($val[$i]->scalarval(), "int"));
			}
			
			$client = new xmlrpc_client($serverUri.'object');
			
			$fields = array(new xmlrpcval("id", "string"), new xmlrpcval("name", "string"));
			
			$msg = new xmlrpcmsg('execute');
			$msg->addParam(new xmlrpcval($db, "string"));
			$msg->addParam(new xmlrpcval($id, "int"));
			$msg->addParam(new xmlrpcval($password, "string"));
			$msg->addParam(new xmlrpcval("omg.sale.chain","string"));
			$msg->addParam(new xmlrpcval("read", "string"));
			$msg->addParam(new xmlrpcval($ides, "array"));
			$msg->addParam(new xmlrpcval($fields, "array"));

			$res = &$client->send($msg);
			if (!$res->faultCode())
			{
				$val = $res->value()->scalarval();
				header('Content-type: text/html; charset=UTF-8') ;
				echo "<html>" ;
				echo "<head>" ;
				//echo "<meta http-equiv='Content-Type' content='text/html; charset=UTF-8'/>" ;
				echo "</head>" ;
				echo "<table width='50%' border='1'>";
				for ($i=0; $i<count($val);$i++)
				{
					echo "<tr>";
					$field = $val[$i]->scalarval();
					$outname = mb_convert_encoding($field['name']->scalarval().' ภาษาไทย','UTF-8','UTF-8') ; 
					//echo $outname.' '.$field['id']->scalarval()."<br/>" ;
					echo "<td width='50%'>".$field['id']->scalarval();
					echo "</td>";
					echo "<td width='50%'>".$outname;
					echo "</td>";
					echo "</tr>";
				}
				echo "</table>";
				echo "</html>";
			}
			else
			{
				echo "Read data error";
			}
		}
		else
		{
			echo "Data is Empty";
		}		
	}
	else
	{
		echo "Connection not establish";
	}

	exit;
?>
